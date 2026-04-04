# DET_C1 System Contracts
## Event Schemas, Real-Time Channels, Module Interface Contracts

**Version:** 1.3 | **Date:** 2026-04-04
**Status:** Detailed Design
**Sources:** SEED F2 (Data Architecture), F3 (Data Flows), F4 (API Contracts), G (Web App Spec), D8 (Engine Formulas), C7 (Time Structure), world_state.py
**Naming authority:** [DET_NAMING_CONVENTIONS.md](DET_NAMING_CONVENTIONS.md) -- all field names, event types, and ID formats defined there

> **Updated 2026-04-03 to reflect BUILD calibration (F1-F104). See CALIBRATION_CHANGE_LOG.md.**

---

# PART 1: EVENT SCHEMA SPECIFICATION

## 1.1 Event Envelope (Common Fields)

Every event in the system conforms to this envelope. The `payload` field varies by event type.

```json
{
  "event_id": "evt_<ulid>",
  "event_type": "<category>.<action>",
  "sim_run_id": "<uuid>",
  "round_num": 3,
  "phase": "A",
  "timestamp": "2026-04-15T14:23:07.412Z",
  "actor_role_id": "dealer",
  "actor_country_id": "columbia",
  "visibility": "PUBLIC",
  "idempotency_key": "act_round3_columbia_v2",
  "snapshot_version": 47,
  "payload": {}
}
```

**Field definitions:**

| Field | Type | Required | Description |
|-------|------|:--------:|-------------|
| `event_id` | string | Yes | Globally unique, time-sortable (ULID). Format: `evt_<26-char-ulid>`. Used as cursor for pagination. See DET_NAMING_CONVENTIONS 1.5. |
| `event_type` | string | Yes | Dot-separated: `<category>.<action>`. Append-only vocabulary. See DET_NAMING_CONVENTIONS 1.4. |
| `sim_run_id` | uuid | Yes | Identifies which SIM instance. |
| `round_num` | int | Yes | Round number (0-8). Canonical name per DET_NAMING_CONVENTIONS 1.1. |
| `phase` | enum | Yes | `"A"` (free action), `"B"` (world update/deployment), `"PRE"` (pre-round), `"POST"` (post-round). |
| `timestamp` | ISO 8601 | Yes | Wall-clock UTC time of event creation. |
| `actor_role_id` | string | Yes | Role that caused the event. `"engine"` for system-generated, `"moderator"` for overrides. |
| `actor_country_id` | string | Yes | Country context. `"global"` for system events. |
| `visibility` | enum | Yes | `"PUBLIC"`, `"COUNTRY"`, `"ROLE"`, `"MODERATOR"`. Determines who receives this event. |
| `idempotency_key` | string | No | Client-provided deduplication key. |
| `snapshot_version` | int | No | State version at time of event. Used for optimistic concurrency. |
| `payload` | object | Yes | Event-type-specific data. See below. |

**Visibility rules (enforced at API layer):**
- `PUBLIC` -- all authenticated users
- `COUNTRY` -- members of `actor_country_id` + moderator
- `ROLE` -- only `actor_role_id` + moderator
- `MODERATOR` -- moderator/admin only

---

## 1.2 Action Events (32 Types)

### Regular Inputs (Phase A deadline)

#### `action.budget_submit`
Submitted once per round per country. Head of state or designated economic authority.

```json
{
  "event_type": "action.budget_submit",
  "visibility": "COUNTRY",
  "payload": {
    "country_id": "columbia",
    "social_allocation": 30.0,
    "military_allocation": 15.0,
    "technology_allocation": 8.0,
    "maintenance_cost": 12.5,
    "total_allocation": 65.5,
    "projected_revenue": 55.8,
    "deficit": 9.7,
    "funded_from_treasury": true,
    "military_production": {
      "ground": { "coins": 6.0, "tier": "normal" },
      "naval": { "coins": 5.0, "tier": "normal" },
      "tactical_air": { "coins": 4.0, "tier": "normal" }
    },
    "tech_rd": {
      "nuclear": 0.0,
      "ai": 8.0
    }
  }
}
```

#### `action.opec_production_set`
OPEC members only. Sets oil production level.

```json
{
  "event_type": "action.opec_production_set",
  "visibility": "PUBLIC",
  "payload": {
    "country_id": "persia",
    "previous_level": "normal",
    "new_level": "low",
    "levels": ["min", "low", "normal", "high", "max"]
  }
}
```

#### `action.tariff_set`
Sets tariff level against a target country.

```json
{
  "event_type": "action.tariff_set",
  "visibility": "PUBLIC",
  "payload": {
    "imposer_country_id": "columbia",
    "target_country_id": "cathay",
    "previous_level": 2,
    "new_level": 3,
    "sector": "all",
    "max_level": 3
  }
}
```

#### `action.sanction_set`
Sets sanction level against a target country.

```json
{
  "event_type": "action.sanction_set",
  "visibility": "PUBLIC",
  "payload": {
    "imposer_country_id": "columbia",
    "target_country_id": "persia",
    "previous_level": 1,
    "new_level": 2,
    "max_level": 3
  }
}
```

#### `action.mobilization_order`
Activates units from finite mobilization pool.

```json
{
  "event_type": "action.mobilization_order",
  "visibility": "COUNTRY",
  "payload": {
    "country_id": "ruthenia",
    "units_mobilized": 3,
    "pool_remaining": 7,
    "deploy_to_zone": "ruthenia_1"
  }
}
```

#### `action.militia_call`
Emergency militia call when homeland under attack. 0.5x combat effectiveness.

```json
{
  "event_type": "action.militia_call",
  "visibility": "COUNTRY",
  "payload": {
    "country_id": "ruthenia",
    "units_raised": 2,
    "max_available": 3,
    "deploy_to_zone": "ruthenia_1",
    "combat_effectiveness": 0.5
  }
}
```

### Military Actions (Real-Time, Phase A)

#### `action.ground_attack`
Dice-based ground combat. Both commanders present. Modifiers hidden from players.

```json
{
  "event_type": "action.ground_attack",
  "visibility": "PUBLIC",
  "payload": {
    "attacker_country_id": "columbia",
    "defender_country_id": "persia",
    "from_zone": "levantia_border",
    "target_zone": "persia_west",
    "attacker_units": {
      "ground": 4,
      "tactical_air": 3
    },
    "defender_units": {
      "ground": 6
    },
    "result": {
      "outcome": "attacker_repelled",
      "attacker_losses": { "ground": 2 },
      "defender_losses": { "ground": 1 },
      "zone_control_changed": false,
      "new_zone_owner": null
    },
    "modifiers_applied": ["terrain_defense", "air_support"]
  }
}
```

#### `action.blockade`
Ground or naval forces blockading a chokepoint. Full/Partial levels.

```json
{
  "event_type": "action.blockade",
  "visibility": "PUBLIC",
  "payload": {
    "blocker_country_id": "persia",
    "chokepoint": "hormuz",
    "blockade_type": "ground",
    "level": "full",
    "units_committed": { "ground": 3 },
    "zone_id": "cp_gulf_gate",
    "oil_impact": 0.60,
    "trade_impact": 0.10,
    "previous_status": "open",
    "new_status": "blocked"
  }
}
```

#### `action.naval_combat`
Ship vs ship engagement. RISK dice at sea.

```json
{
  "event_type": "action.naval_combat",
  "visibility": "PUBLIC",
  "payload": {
    "attacker_country_id": "columbia",
    "defender_country_id": "cathay",
    "zone_id": "w(17,7)",
    "attacker_ships": 5,
    "defender_ships": 3,
    "result": {
      "outcome": "attacker_wins",
      "attacker_losses": 1,
      "defender_losses": 3,
      "embarked_units_lost": { "ground": 0 },
      "zone_control_changed": true
    }
  }
}
```

#### `action.naval_bombardment`
Safe, slow bombardment. 10% hit per ship per round.

```json
{
  "event_type": "action.naval_bombardment",
  "visibility": "PUBLIC",
  "payload": {
    "attacker_country_id": "columbia",
    "target_zone": "persia_coast",
    "ships_firing": 4,
    "hit_rate_per_ship": 0.10,
    "hits_achieved": 1,
    "target_units_destroyed": { "ground": 1 }
  }
}
```

#### `action.air_strike`
Air strike with AD interception. 15% hit per surviving aircraft.

```json
{
  "event_type": "action.air_strike",
  "visibility": "PUBLIC",
  "payload": {
    "attacker_country_id": "columbia",
    "target_zone": "persia_west",
    "aircraft_deployed": 6,
    "air_defense_units": 2,
    "aircraft_intercepted": 1,
    "aircraft_surviving": 5,
    "hit_rate_per_survivor": 0.15,
    "hits_achieved": 1,
    "target_units_destroyed": { "ground": 1 }
  }
}
```

#### `action.strategic_missile`
5-tier escalation. 10-minute authorization clock.

```json
{
  "event_type": "action.strategic_missile",
  "visibility": "PUBLIC",
  "payload": {
    "attacker_country_id": "columbia",
    "target_zone": "persia_west",
    "missile_type": "conventional",
    "tier": 2,
    "missiles_launched": 3,
    "authorization_role_id": "dealer",
    "authorization_timestamp": "2026-04-15T14:13:07Z",
    "result": {
      "hits": 2,
      "target_units_destroyed": { "ground": 2 },
      "infrastructure_damage": 0.0
    },
    "nuclear": false
  }
}
```

#### `action.nuclear_strike`
Nuclear weapon deployment. Tier 4-5. Changes sim permanently.

```json
{
  "event_type": "action.nuclear_strike",
  "visibility": "PUBLIC",
  "payload": {
    "attacker_country_id": "columbia",
    "target_zone": "cathay_coastal",
    "warheads_launched": 1,
    "authorization_role_id": "dealer",
    "authorization_timestamp": "2026-04-15T14:10:00Z",
    "authorization_chain": ["dealer", "pentagon"],
    "result": {
      "zone_destroyed": true,
      "casualties_military": 8,
      "casualties_civilian": true,
      "nuclear_used_this_sim": true,
      "global_stability_impact": -2.0,
      "global_market_impact": -30
    }
  }
}
```

#### `action.troop_deployment`
Unit redeployment during Phase B.

```json
{
  "event_type": "action.troop_deployment",
  "visibility": "COUNTRY",
  "payload": {
    "country_id": "columbia",
    "deployments": [
      {
        "unit_type": "ground",
        "count": 3,
        "from_zone": "col_continental",
        "to_zone": "col_pacific",
        "transit_rounds": 0,
        "available_round": 3
      },
      {
        "unit_type": "naval",
        "count": 2,
        "from_zone": "col_continental",
        "to_zone": "w(12,5)",
        "transit_rounds": 1,
        "available_round": 4
      }
    ]
  }
}
```

### Intelligence / Covert Actions (Phase A, Limited Pools)

#### `action.intelligence_request`
Per-individual pool. Always returns an answer.

```json
{
  "event_type": "action.intelligence_request",
  "visibility": "ROLE",
  "payload": {
    "requester_role_id": "pentagon",
    "target_country_id": "cathay",
    "target_domain": "military",
    "question": "Current naval force deployment in South China Sea",
    "pool_remaining": 2,
    "result": {
      "answer": "Cathay has 8 naval units deployed across zones w(16,7) and w(17,7)",
      "accuracy": "exact",
      "noise_applied": false,
      "detection_risk": 0.10,
      "detected": false
    }
  }
}
```

#### `action.sabotage`
2-3 cards per game. 40% base success rate.

```json
{
  "event_type": "action.sabotage",
  "visibility": "MODERATOR",
  "payload": {
    "orderer_role_id": "pentagon",
    "target_country_id": "persia",
    "target_type": "oil_infrastructure",
    "cards_remaining": 1,
    "base_success_rate": 0.40,
    "modifiers": [],
    "result": {
      "success": true,
      "effect": "oil_production_disrupted",
      "duration_rounds": 1,
      "detection": {
        "detected": false,
        "attribution": null
      }
    }
  }
}
```

**Note:** Successful sabotage creates a separate PUBLIC event describing the effect without attribution. The MODERATOR-visibility event records the full details.

#### `action.cyber_attack`
2-3 cards per game. 50% base success. Low impact.

```json
{
  "event_type": "action.cyber_attack",
  "visibility": "MODERATOR",
  "payload": {
    "orderer_role_id": "helmsman",
    "target_country_id": "columbia",
    "target_type": "financial_systems",
    "cards_remaining": 2,
    "base_success_rate": 0.50,
    "result": {
      "success": true,
      "effect": "market_indexes_reduction",
      "impact_value": -5,
      "duration_rounds": 1,
      "detection": {
        "detected": true,
        "attribution": "suspected_cathay"
      }
    }
  }
}
```

#### `action.disinformation`
2-3 cards per game. 55% base success. Hardest to trace.

```json
{
  "event_type": "action.disinformation",
  "visibility": "MODERATOR",
  "payload": {
    "orderer_role_id": "commissar",
    "target_country_id": "ruthenia",
    "target_type": "political_support",
    "cards_remaining": 1,
    "base_success_rate": 0.55,
    "result": {
      "success": true,
      "effect": "support_reduction",
      "impact_value": -3.0,
      "detection": {
        "detected": false,
        "attribution": null
      }
    }
  }
}
```

#### `action.election_meddling`
1 card per game. 2-5% impact on election outcome.

```json
{
  "event_type": "action.election_meddling",
  "visibility": "MODERATOR",
  "payload": {
    "orderer_role_id": "commissar",
    "target_country_id": "columbia",
    "target_election": "columbia_presidential",
    "cards_remaining": 0,
    "base_impact_range": [0.02, 0.05],
    "result": {
      "impact_pct": 0.03,
      "favored_candidate": "anchor",
      "detection": {
        "detected": false,
        "attribution": null
      }
    }
  }
}
```

### Political Actions (Phase A)

#### `action.arrest`
Moderator present. Target out of play until released.

```json
{
  "event_type": "action.arrest",
  "visibility": "PUBLIC",
  "payload": {
    "orderer_role_id": "dealer",
    "target_role_id": "dissident_leader",
    "country_id": "columbia",
    "authority": "head_of_state",
    "result": {
      "arrested": true,
      "target_new_status": "arrested",
      "powers_suspended": true,
      "release_condition": "moderator_or_order"
    }
  }
}
```

#### `action.fire_role`
Moderator present. Immediate power loss.

```json
{
  "event_type": "action.fire_role",
  "visibility": "PUBLIC",
  "payload": {
    "orderer_role_id": "dealer",
    "target_role_id": "pentagon",
    "country_id": "columbia",
    "authority": "head_of_state",
    "result": {
      "fired": true,
      "target_new_status": "fired",
      "powers_revoked": ["authorize_attack", "deploy_units"],
      "successor_role_id": null
    }
  }
}
```

#### `action.propaganda`
Coins for support boost. Diminishing returns.

```json
{
  "event_type": "action.propaganda",
  "visibility": "COUNTRY",
  "payload": {
    "orderer_role_id": "commissar",
    "country_id": "sarmatia",
    "coins_spent": 2.0,
    "source": "personal_coins",
    "result": {
      "support_change": 3.0,
      "new_support": 53.0,
      "diminishing_returns_factor": 0.75,
      "cumulative_spend_this_sim": 5.0
    }
  }
}
```

#### `action.assassination`
1 card per game. Probability-based.

```json
{
  "event_type": "action.assassination",
  "visibility": "MODERATOR",
  "payload": {
    "orderer_role_id": "shah",
    "target_role_id": "opposition_leader",
    "cards_remaining": 0,
    "base_success_rate": 0.30,
    "result": {
      "success": false,
      "target_new_status": "active",
      "detection": {
        "detected": true,
        "attribution": "persia"
      },
      "consequences": {
        "diplomatic_fallout": true,
        "stability_impact_orderer": -1.0
      }
    }
  }
}
```

#### `action.coup_attempt`
Two roles conspire. Betrayal possible.

```json
{
  "event_type": "action.coup_attempt",
  "visibility": "PUBLIC",
  "payload": {
    "primary_conspirator_role_id": "general_x",
    "secondary_conspirator_role_id": "minister_y",
    "target_country_id": "persia",
    "target_head_of_state": "shah",
    "betrayal": false,
    "result": {
      "success": true,
      "old_head_of_state": "shah",
      "new_head_of_state": "general_x",
      "shah_new_status": "arrested",
      "stability_impact": -2.0,
      "support_impact": -5.0
    }
  }
}
```

#### `action.protest`
Automatic when stability thresholds crossed, or stimulated via card.

```json
{
  "event_type": "action.protest",
  "visibility": "PUBLIC",
  "payload": {
    "country_id": "ruthenia",
    "trigger": "stability_threshold",
    "stimulated_by_role_id": null,
    "stability_at_trigger": 4.8,
    "threshold": 5.0,
    "result": {
      "severity": "moderate",
      "stability_impact": -0.5,
      "support_impact": -3.0,
      "suppressed": false
    }
  }
}
```

#### `action.impeachment`
Columbia/Ruthenia only. Parliament votes.

```json
{
  "event_type": "action.impeachment",
  "visibility": "PUBLIC",
  "payload": {
    "country_id": "columbia",
    "target_role_id": "dealer",
    "initiated_by_role_id": "senator_x",
    "parliament_votes": {
      "for": 3,
      "against": 2,
      "threshold": 3
    },
    "result": {
      "impeached": true,
      "target_new_status": "fired",
      "successor_role_id": "volt",
      "succession_rule": "vice_president"
    }
  }
}
```

### Transactions (Phase A, Bilateral, Irreversible)

#### `action.transaction_propose`
Initial proposal for any bilateral transaction.

```json
{
  "event_type": "action.transaction_propose",
  "visibility": "ROLE",
  "payload": {
    "transaction_id": "txn_<ulid>",
    "transaction_type": "transfer_coins",
    "proposer_role_id": "dealer",
    "counterparty_role_id": "helmsman",
    "terms": {
      "from_country": "columbia",
      "to_country": "cathay",
      "amount": 10.0,
      "conditions": "In exchange for lifting rare earth restrictions on Columbia"
    },
    "expires_at": "2026-04-15T15:00:00Z"
  }
}
```

#### `action.transaction_confirm`
Counterparty accepts or rejects.

```json
{
  "event_type": "action.transaction_confirm",
  "visibility": "COUNTRY",
  "payload": {
    "transaction_id": "txn_<ulid>",
    "transaction_type": "transfer_coins",
    "accepted": true,
    "confirmer_role_id": "helmsman",
    "state_changes": [
      { "path": "countries.columbia.economic.treasury", "old": 42.3, "new": 32.3 },
      { "path": "countries.cathay.economic.treasury", "old": 85.0, "new": 95.0 }
    ]
  }
}
```

#### `action.agreement_sign`
Armistice, peace, alliance, custom bilateral or multilateral agreement.

```json
{
  "event_type": "action.agreement_sign",
  "visibility": "PUBLIC",
  "payload": {
    "agreement_id": "agr_<ulid>",
    "agreement_type": "peace_treaty",
    "signatories": ["columbia", "persia"],
    "signatory_roles": ["dealer", "shah"],
    "terms_text": "Ceasefire effective immediately. Columbia withdraws from Persia West within 1 round.",
    "public": true,
    "secret_terms": null
  }
}
```

**Note:** Agreements with `"public": false` have visibility `"ROLE"` restricted to signatory roles.

#### `action.organization_create`
New international organization. 2+ countries. Public event.

```json
{
  "event_type": "action.organization_create",
  "visibility": "PUBLIC",
  "payload": {
    "organization_id": "org_<ulid>",
    "name": "Eastern Economic Cooperation",
    "founding_members": ["cathay", "indus", "formosa"],
    "founding_roles": ["helmsman", "prime_minister_indus", "president_formosa"],
    "decision_rule": "majority",
    "chair_role_id": "helmsman",
    "description": "Economic cooperation bloc for Eastern nations"
  }
}
```

### Communication Actions

#### `action.public_statement`
Via moderator. Physical speech.

```json
{
  "event_type": "action.public_statement",
  "visibility": "PUBLIC",
  "payload": {
    "speaker_role_id": "dealer",
    "country_id": "columbia",
    "statement_type": "speech",
    "content": "Columbia stands with Ruthenia against aggression. We call on all nations to join us.",
    "context": "opening_ceremony"
  }
}
```

#### `action.meeting_call`
Calls an organization meeting. Physical meeting; app notifies members.

```json
{
  "event_type": "action.meeting_call",
  "visibility": "PUBLIC",
  "payload": {
    "caller_role_id": "dealer",
    "organization_id": "nato_western_treaty",
    "meeting_type": "emergency",
    "agenda": "Response to Sarmatia escalation",
    "invited_roles": ["dealer", "chancellor", "prime_minister_uk"],
    "location_hint": "Room B, Table 3"
  }
}
```

#### `action.election_nominate`
Nomination for scheduled election. 10 minutes before election.

```json
{
  "event_type": "action.election_nominate",
  "visibility": "PUBLIC",
  "payload": {
    "election_id": "columbia_presidential",
    "nominee_role_id": "volt",
    "nominator_role_id": "senator_x",
    "country_id": "columbia",
    "round": 5
  }
}
```

#### `action.court_proceeding`

Triggered when a participant files a court complaint in a democracy.

```json
{
  "event_type": "action.court_proceeding",
  "visibility": "PUBLIC",
  "payload": {
    "run_id": "uuid",
    "round": 3,
    "country_id": "columbia",
    "plaintiff_role_id": "tribune",
    "defendant_role_id": "dealer",
    "plaintiff_arguments": "The President arrested me without legal basis...",
    "defendant_arguments": "National security required immediate action...",
    "verdict": "OVERTURNED",
    "verdict_reasoning": "Arrest lacked evidence of actual threat to national security."
  }
}
```

---

## 1.3 Engine Events

#### `engine.round_start`
Emitted when a new round begins.

```json
{
  "event_type": "engine.round_start",
  "actor_role_id": "engine",
  "actor_country_id": "global",
  "visibility": "PUBLIC",
  "payload": {
    "round": 3,
    "scenario_time": "H2 2027",
    "phase": "A",
    "phase_a_duration_minutes": 60,
    "scheduled_events": [
      { "type": "election", "subtype": "ruthenia_wartime", "country": "ruthenia" }
    ],
    "active_wars": [
      { "attacker": "sarmatia", "defender": "ruthenia", "theater": "eastern_ereb" }
    ]
  }
}
```

#### `engine.round_end`
Emitted when a round is frozen.

```json
{
  "event_type": "engine.round_end",
  "actor_role_id": "engine",
  "actor_country_id": "global",
  "visibility": "PUBLIC",
  "payload": {
    "round": 3,
    "snapshot_frozen": true,
    "events_this_round": 47,
    "next_round": 4
  }
}
```

#### `engine.world_update`
Batch results from World Model Engine (Phase B). Per-country summary pushed to appropriate visibility levels.

```json
{
  "event_type": "engine.world_update",
  "actor_role_id": "engine",
  "actor_country_id": "global",
  "visibility": "MODERATOR",
  "payload": {
    "round": 3,
    "processing_time_ms": 2340,
    "pass_1_deterministic": {
      "oil_price": { "old": 95.2, "new": 112.5 },
      "countries_processed": 20
    },
    "pass_2_ai_adjustments": {
      "adjustments_applied": 4,
      "total_gdp_delta_pct": -0.8
    },
    "pass_3_coherence": {
      "flags_raised": 2,
      "auto_fixed": 1
    },
    "narrative_generated": true,
    "expert_panel_complete": true
  }
}
```

**Note:** A filtered `engine.country_update` event at COUNTRY visibility is also generated per country:

```json
{
  "event_type": "engine.country_update",
  "actor_role_id": "engine",
  "actor_country_id": "columbia",
  "visibility": "COUNTRY",
  "payload": {
    "round": 3,
    "country_id": "columbia",
    "economic": {
      "gdp": { "old": 274.0, "new": 278.5 },
      "treasury": { "old": 38.1, "new": 42.3 },
      "inflation": { "old": 4.8, "new": 5.2 },
      "revenue": 55.8,
      "economic_state": "normal"
    },
    "military": {
      "units_produced": { "ground": 2, "naval": 1 },
      "maintenance_cost": 12.5
    },
    "political": {
      "stability": { "old": 7.2, "new": 7.0 },
      "political_support": { "old": 39.0, "new": 38.0 }
    },
    "technology": {
      "ai_level": 3,
      "ai_rd_progress": { "old": 0.60, "new": 0.80 }
    }
  }
}
```

#### `engine.election_result`
Emitted after scheduled election processing.

```json
{
  "event_type": "engine.election_result",
  "actor_role_id": "engine",
  "actor_country_id": "columbia",
  "visibility": "PUBLIC",
  "payload": {
    "election_type": "columbia_midterms",
    "country_id": "columbia",
    "round": 2,
    "candidates": [
      { "party": "dem", "vote_pct": 52.0 },
      { "party": "rep", "vote_pct": 48.0 }
    ],
    "winner": "dem",
    "margin": 4.0,
    "effects": {
      "political_support": 5.0,
      "dem_rep_split": { "dem": 52.0, "rep": 48.0 }
    }
  }
}
```

#### `engine.combat_result`
Generated by Live Action Engine after combat resolution.

```json
{
  "event_type": "engine.combat_result",
  "actor_role_id": "engine",
  "actor_country_id": "global",
  "visibility": "PUBLIC",
  "payload": {
    "combat_type": "ground",
    "attacker_country_id": "columbia",
    "defender_country_id": "persia",
    "zone_id": "persia_west",
    "outcome": "attacker_repelled",
    "attacker_losses": { "ground": 2 },
    "defender_losses": { "ground": 1 },
    "zone_control_changed": false,
    "war_context": {
      "war_theater": "mashriq",
      "war_duration_rounds": 3
    }
  }
}
```

#### `engine.production_complete`
Military production results from Phase B.

```json
{
  "event_type": "engine.production_complete",
  "actor_role_id": "engine",
  "actor_country_id": "columbia",
  "visibility": "COUNTRY",
  "payload": {
    "country_id": "columbia",
    "round": 3,
    "units_produced": {
      "ground": { "count": 2, "cost": 6.0, "tier": "normal" },
      "naval": { "count": 1, "cost": 5.0, "tier": "normal" },
      "tactical_air": { "count": 1, "cost": 4.0, "tier": "normal" }
    },
    "strategic_missiles_auto": 0,
    "total_production_cost": 15.0
  }
}
```

#### `engine.tech_advance`
Technology level advancement.

```json
{
  "event_type": "engine.tech_advance",
  "actor_role_id": "engine",
  "actor_country_id": "cathay",
  "visibility": "PUBLIC",
  "payload": {
    "country_id": "cathay",
    "domain": "ai",
    "old_level": 3,
    "new_level": 4,
    "effects": {
      "growth_rate_bonus": 0.030,
      "combat_bonus": 2,
      "description": "Cathay achieves AI Level 4 — significant economic and military advantage"
    }
  }
}
```

#### `engine.coherence_flag`
Raised during Pass 3 coherence check.

```json
{
  "event_type": "engine.coherence_flag",
  "actor_role_id": "engine",
  "actor_country_id": "global",
  "visibility": "MODERATOR",
  "payload": {
    "severity": "HIGH",
    "country_id": "persia",
    "description": "GDP growth positive during economic collapse -- forced to -2%",
    "auto_fixed": true,
    "field": "gdp_growth_rate",
    "old_value": 0.01,
    "new_value": -0.02
  }
}
```

---

### 1.3.b Round Runner Events

*Added 2026-04-04 for AI Participant round runner integration. These events are emitted by `app/engine/agents/runner.py` (RoundReport / SimReport flow) and supplement the Engine Events above. `engine.round_start` payload below extends the existing `engine.round_start` schema with runner-specific fields (`active_agents`, `world_state_summary`).*

#### `engine.round_start` (runner variant)
Emitted by the round runner at the beginning of a round to announce active AI agents and snapshot world state.

```json
{
  "event_type": "engine.round_start",
  "actor_role_id": "engine",
  "actor_country_id": "global",
  "visibility": "PUBLIC",
  "payload": {
    "round_num": 3,
    "active_agents": ["columbia_head", "persia_head", "ruthenia_head"],
    "world_state_summary": "Round 3 H2 2027: 1 active war (Mashriq), oil $112/bbl, 20 countries active"
  }
}
```

#### `engine.round_complete`
Emitted by the round runner when a round finishes (distinct from `engine.round_end` which marks snapshot freeze). Reports aggregate runner metrics.

```json
{
  "event_type": "engine.round_complete",
  "actor_role_id": "engine",
  "actor_country_id": "global",
  "visibility": "PUBLIC",
  "payload": {
    "round_num": 3,
    "duration_seconds": 187.4,
    "actions_count": 42,
    "conversations_count": 11,
    "transactions_count": 6,
    "summary": "Round 3 complete: 42 actions, 11 conversations, 6 transactions"
  }
}
```

#### `engine.active_loop_tick`
Emitted on each iteration of the active loop during Phase A.

```json
{
  "event_type": "engine.active_loop_tick",
  "actor_role_id": "engine",
  "actor_country_id": "global",
  "visibility": "MODERATOR",
  "payload": {
    "round_num": 3,
    "tick_num": 4,
    "agents_decided": 7,
    "actions_taken": 3,
    "conversations_matched": 2
  }
}
```

#### `engine.conversation_matched`
Emitted when two agents are paired for a bilateral conversation.

```json
{
  "event_type": "engine.conversation_matched",
  "actor_role_id": "engine",
  "actor_country_id": "global",
  "visibility": "MODERATOR",
  "payload": {
    "role_a": "columbia_head",
    "role_b": "persia_head",
    "round_num": 3,
    "tick_num": 4
  }
}
```

#### `engine.transaction_proposed`
Emitted when an agent proposes a transaction (deal) to a counterpart.

```json
{
  "event_type": "engine.transaction_proposed",
  "actor_role_id": "engine",
  "actor_country_id": "global",
  "visibility": "MODERATOR",
  "payload": {
    "transaction_type": "arms_sale",
    "proposer_role_id": "columbia_head",
    "counterpart_role_id": "persia_head",
    "terms": { "coins": 12.0, "units": { "ground": 3 } },
    "reasoning": "Strengthen Persia to balance Ruthenia expansion"
  }
}
```

#### `engine.transaction_resolved`
Emitted when a proposed transaction is evaluated by the counterpart.

```json
{
  "event_type": "engine.transaction_resolved",
  "actor_role_id": "engine",
  "actor_country_id": "global",
  "visibility": "MODERATOR",
  "payload": {
    "transaction_id": "txn_<ulid>",
    "decision": "accept",
    "reasoning": "Terms align with defense posture; accept to secure supply line"
  }
}
```

#### `engine.mandatory_submitted`
Emitted when an agent submits round-end mandatory inputs (budget, tariffs, sanctions, OPEC production).

```json
{
  "event_type": "engine.mandatory_submitted",
  "actor_role_id": "engine",
  "actor_country_id": "columbia",
  "visibility": "COUNTRY",
  "payload": {
    "role_id": "columbia_head",
    "country_id": "columbia",
    "budget": { "social_allocation": 30.0, "military_allocation": 15.0, "technology_allocation": 8.0 },
    "tariffs": { "persia": 10.0, "ruthenia": 25.0 },
    "sanctions": ["ruthenia"],
    "opec_production": null
  }
}
```

#### `engine.agent_reflection`
Emitted when an agent completes post-round reflection updating its 4-block memory.

```json
{
  "event_type": "engine.agent_reflection",
  "actor_role_id": "engine",
  "actor_country_id": "columbia",
  "visibility": "MODERATOR",
  "payload": {
    "role_id": "columbia_head",
    "blocks_updated": ["situation", "strategy", "relationships"],
    "summary": "Updated strategy to prioritize Mashriq de-escalation; flagged Ruthenia as hostile"
  }
}
```

---

## 1.4 System Events

#### `system.player_login`

```json
{
  "event_type": "system.player_login",
  "actor_role_id": "dealer",
  "actor_country_id": "columbia",
  "visibility": "MODERATOR",
  "payload": {
    "user_id": "user_<uuid>",
    "user_type": "human",
    "device_type": "mobile",
    "session_id": "sess_<uuid>"
  }
}
```

#### `system.role_assigned`

```json
{
  "event_type": "system.role_assigned",
  "actor_role_id": "moderator",
  "actor_country_id": "global",
  "visibility": "MODERATOR",
  "payload": {
    "user_id": "user_<uuid>",
    "role_id": "dealer",
    "country_id": "columbia",
    "user_type": "human",
    "access_level": "participant"
  }
}
```

#### `system.phase_change`

```json
{
  "event_type": "system.phase_change",
  "actor_role_id": "engine",
  "actor_country_id": "global",
  "visibility": "PUBLIC",
  "payload": {
    "round": 3,
    "old_phase": "A",
    "new_phase": "B",
    "timestamp": "2026-04-15T15:30:00Z",
    "next_phase_duration_minutes": 15
  }
}
```

#### `system.moderator_override`

```json
{
  "event_type": "system.moderator_override",
  "actor_role_id": "moderator",
  "actor_country_id": "global",
  "visibility": "MODERATOR",
  "payload": {
    "overrides": [
      {
        "path": "countries.ruthenia.political.stability",
        "old_value": 6.0,
        "new_value": 4.0,
        "reason": "Manual adjustment for off-screen political crisis"
      }
    ],
    "warnings_generated": ["Stability set to 4.0 -- triggers protest_probable threshold"]
  }
}
```

#### `system.moderator_announcement`

```json
{
  "event_type": "system.moderator_announcement",
  "actor_role_id": "moderator",
  "actor_country_id": "global",
  "visibility": "PUBLIC",
  "payload": {
    "announcement_type": "event_injection",
    "content": "Breaking: Earthquake in Indus region. Infrastructure damage assessment underway.",
    "affects_countries": ["indus"]
  }
}
```

#### `system.timer_update`

```json
{
  "event_type": "system.timer_update",
  "actor_role_id": "engine",
  "actor_country_id": "global",
  "visibility": "PUBLIC",
  "payload": {
    "round": 3,
    "phase": "A",
    "seconds_remaining": 1200,
    "extended": false,
    "extension_minutes": 0
  }
}
```

---

## 1.5 Communication Events

#### `comms.message_sent`

```json
{
  "event_type": "comms.message_sent",
  "actor_role_id": "dealer",
  "actor_country_id": "columbia",
  "visibility": "ROLE",
  "payload": {
    "channel_id": "team_columbia",
    "channel_type": "country_team",
    "message_id": "msg_<ulid>",
    "content": "Team, we need to discuss the Cathay tariff response.",
    "recipients": ["dealer", "pentagon", "wall_street", "senator_1", "senator_2"]
  }
}
```

#### `comms.meeting_started`

```json
{
  "event_type": "comms.meeting_started",
  "actor_role_id": "dealer",
  "actor_country_id": "columbia",
  "visibility": "PUBLIC",
  "payload": {
    "meeting_id": "mtg_<ulid>",
    "meeting_type": "organization",
    "organization_id": "nato_western_treaty",
    "participants": ["dealer", "chancellor", "prime_minister_uk"],
    "physical_location": "Room B, Table 3"
  }
}
```

#### `comms.public_broadcast`

```json
{
  "event_type": "comms.public_broadcast",
  "actor_role_id": "moderator",
  "actor_country_id": "global",
  "visibility": "PUBLIC",
  "payload": {
    "broadcast_type": "news_flash",
    "content": "OPEC+ announces production cut to 'low' level. Oil markets react.",
    "source": "moderator"
  }
}
```

---

## 1.6 AI Events

#### `ai.decision_made`

```json
{
  "event_type": "ai.decision_made",
  "actor_role_id": "helmsman",
  "actor_country_id": "cathay",
  "visibility": "MODERATOR",
  "payload": {
    "ai_agent_id": "agent_helmsman",
    "model_id": "claude-opus-4-6",
    "round": 3,
    "phase": "A",
    "actions_decided": [
      { "action_type": "tariff_set", "target": "columbia", "level": 3 },
      { "action_type": "budget_submit", "summary": "Heavy naval + AI R&D" }
    ],
    "negotiations_initiated": [
      { "target_role": "shah", "summary": "Anti-Columbia economic bloc" }
    ],
    "internal_reasoning": "Columbia's tariff escalation signals containment. Priority: naval dominance for Formosa, alternative trade bloc, AI L4.",
    "processing_time_ms": 4200,
    "tokens_used": { "input": 8500, "output": 1200 }
  }
}
```

#### `ai.context_updated`

```json
{
  "event_type": "ai.context_updated",
  "actor_role_id": "engine",
  "actor_country_id": "global",
  "visibility": "MODERATOR",
  "payload": {
    "ai_agent_id": "agent_helmsman",
    "round": 3,
    "context_snapshot": {
      "visible_state_hash": "sha256:abc123...",
      "recent_events_count": 12,
      "conversation_history_turns": 3,
      "available_actions_count": 15
    }
  }
}
```

#### `ai.argus_conversation`

```json
{
  "event_type": "ai.argus_conversation",
  "actor_role_id": "dealer",
  "actor_country_id": "columbia",
  "visibility": "MODERATOR",
  "payload": {
    "participant_user_id": "user_<uuid>",
    "argus_phase": "MID",
    "conversation_turn": 3,
    "participant_message_summary": "Asked about tariff escalation risks",
    "argus_response_summary": "Outlined GDP impact scenarios for tariff war",
    "voice_audio_url": "https://storage.example.com/argus/audio_<uuid>.mp3",
    "processing_time_ms": 1800
  }
}
```

---

## 1.7 Event Type Index

Complete list of all event types for validation and schema registry.

| Category | Event Type | Visibility |
|----------|-----------|------------|
| **Action: Regular** | `action.budget_submit` | COUNTRY |
| | `action.opec_production_set` | PUBLIC |
| | `action.tariff_set` | PUBLIC |
| | `action.sanction_set` | PUBLIC |
| | `action.mobilization_order` | COUNTRY |
| | `action.militia_call` | COUNTRY |
| **Action: Military** | `action.ground_attack` | PUBLIC |
| | `action.blockade` | PUBLIC |
| | `action.naval_combat` | PUBLIC |
| | `action.naval_bombardment` | PUBLIC |
| | `action.air_strike` | PUBLIC |
| | `action.strategic_missile` | PUBLIC |
| | `action.nuclear_strike` | PUBLIC |
| | `action.troop_deployment` | COUNTRY |
| **Action: Covert** | `action.intelligence_request` | ROLE |
| | `action.sabotage` | MODERATOR |
| | `action.cyber_attack` | MODERATOR |
| | `action.disinformation` | MODERATOR |
| | `action.election_meddling` | MODERATOR |
| **Action: Political** | `action.arrest` | PUBLIC |
| | `action.fire_role` | PUBLIC |
| | `action.propaganda` | COUNTRY |
| | `action.assassination` | MODERATOR |
| | `action.coup_attempt` | PUBLIC |
| | `action.protest` | PUBLIC |
| | `action.impeachment` | PUBLIC |
| | `action.court_proceeding` | PUBLIC |
| **Action: Transaction** | `action.transaction_propose` | ROLE |
| | `action.transaction_confirm` | COUNTRY |
| | `action.agreement_sign` | PUBLIC* |
| | `action.organization_create` | PUBLIC |
| **Action: Communication** | `action.public_statement` | PUBLIC |
| | `action.meeting_call` | PUBLIC |
| | `action.election_nominate` | PUBLIC |
| **Engine** | `engine.round_start` | PUBLIC |
| | `engine.round_end` | PUBLIC |
| | `engine.world_update` | MODERATOR |
| | `engine.country_update` | COUNTRY |
| | `engine.election_result` | PUBLIC |
| | `engine.combat_result` | PUBLIC |
| | `engine.production_complete` | COUNTRY |
| | `engine.tech_advance` | PUBLIC |
| | `engine.coherence_flag` | MODERATOR |
| **Engine: Runner** (2026-04-04) | `engine.round_complete` | PUBLIC |
| | `engine.active_loop_tick` | MODERATOR |
| | `engine.conversation_matched` | MODERATOR |
| | `engine.transaction_proposed` | MODERATOR |
| | `engine.transaction_resolved` | MODERATOR |
| | `engine.mandatory_submitted` | COUNTRY |
| | `engine.agent_reflection` | MODERATOR |
| **System** | `system.player_login` | MODERATOR |
| | `system.role_assigned` | MODERATOR |
| | `system.phase_change` | PUBLIC |
| | `system.moderator_override` | MODERATOR |
| | `system.moderator_announcement` | PUBLIC |
| | `system.timer_update` | PUBLIC |
| **Comms** | `comms.message_sent` | ROLE |
| | `comms.meeting_started` | PUBLIC |
| | `comms.public_broadcast` | PUBLIC |
| **AI** | `ai.decision_made` | MODERATOR |
| | `ai.context_updated` | MODERATOR |
| | `ai.argus_conversation` | MODERATOR |

*`action.agreement_sign` is PUBLIC when `public: true`, ROLE when `public: false`.

---

# PART 2: REAL-TIME CHANNEL MAP (C2)

## 2.1 Channel Architecture

All real-time communication uses Supabase Realtime (WebSocket). Channels follow a hierarchical naming convention. Authentication is via Supabase JWT with role claims.

## 2.2 Channel Definitions

### `sim:{sim_id}:world`

| Property | Value |
|----------|-------|
| **Purpose** | Public world state updates visible to all participants |
| **Subscribers** | All authenticated users (participants, moderator, spectators, AI agents) |
| **Message types** | `state_update`, `event` (PUBLIC visibility only) |
| **Frequency** | Real-time during Phase A (on each public action); batch after Phase B |
| **Example message** | |

```json
{
  "type": "state_update",
  "channel": "sim:abc123:world",
  "payload": {
    "round": 3,
    "changes": [
      {
        "path": "oil_price",
        "old": 95.2,
        "new": 112.5,
        "reason": "round_processing"
      },
      {
        "path": "chokepoint_status.hormuz",
        "old": "open",
        "new": "blocked",
        "reason": "blockade_action"
      }
    ],
    "snapshot_version": 48
  }
}
```

### `sim:{sim_id}:country:{country_id}`

| Property | Value |
|----------|-------|
| **Purpose** | Country-specific state updates |
| **Subscribers** | All roles belonging to `country_id` + moderator |
| **Message types** | `state_update`, `event` (COUNTRY + PUBLIC visibility) |
| **Frequency** | Real-time on country-affecting actions; batch after Phase B |
| **Auth rule** | JWT `country_id` must match channel `country_id`, OR `access_level == moderator` |
| **Example message** | |

```json
{
  "type": "state_update",
  "channel": "sim:abc123:country:columbia",
  "payload": {
    "round": 3,
    "changes": [
      {
        "path": "economic.treasury",
        "old": 42.3,
        "new": 32.3,
        "reason": "transaction_executed"
      }
    ],
    "snapshot_version": 49
  }
}
```

### `sim:{sim_id}:role:{role_id}`

| Property | Value |
|----------|-------|
| **Purpose** | Private updates for a specific role |
| **Subscribers** | The single user assigned to `role_id` + moderator |
| **Message types** | `event` (ROLE visibility), `state_update` (personal_coins, status changes) |
| **Frequency** | Sporadic -- on intelligence results, covert op results, personal transactions |
| **Auth rule** | JWT `role_id` must match channel `role_id`, OR `access_level == moderator` |
| **Example message** | |

```json
{
  "type": "event",
  "channel": "sim:abc123:role:pentagon",
  "payload": {
    "event_id": "evt_xyz789",
    "event_type": "action.intelligence_request",
    "round": 3,
    "summary": "Intelligence report received: Cathay naval deployment in South China Sea",
    "details": {
      "target_country_id": "cathay",
      "domain": "military",
      "answer": "8 naval units across w(16,7) and w(17,7)"
    }
  }
}
```

### `sim:{sim_id}:facilitator`

| Property | Value |
|----------|-------|
| **Purpose** | Moderator-only updates: engine diagnostics, coherence flags, AI agent status, alerts |
| **Subscribers** | Users with `access_level == moderator` or `access_level == admin` |
| **Message types** | `event` (MODERATOR visibility), `state_update`, `alert`, `engine_status` |
| **Frequency** | Continuous -- every action generates a moderator-visible trace |
| **Example message** | |

```json
{
  "type": "alert",
  "channel": "sim:abc123:facilitator",
  "payload": {
    "alert_type": "nuclear_authorization",
    "severity": "CRITICAL",
    "description": "Columbia has initiated nuclear authorization clock (10 min)",
    "country_id": "columbia",
    "role_id": "dealer",
    "countdown_expires_at": "2026-04-15T14:33:07Z"
  }
}
```

### `sim:{sim_id}:phase`

| Property | Value |
|----------|-------|
| **Purpose** | Phase change announcements |
| **Subscribers** | All authenticated users |
| **Message types** | `phase_change`, `timer` |
| **Frequency** | Phase transitions (2-3 per round) + timer ticks every 60 seconds |
| **Example message** | |

```json
{
  "type": "phase_change",
  "channel": "sim:abc123:phase",
  "payload": {
    "round": 3,
    "old_phase": "A",
    "new_phase": "B",
    "message": "Phase A complete. World model processing begins.",
    "next_phase_duration_minutes": 15
  }
}
```

### `sim:{sim_id}:alerts`

| Property | Value |
|----------|-------|
| **Purpose** | High-priority global alerts that demand immediate attention |
| **Subscribers** | All authenticated users |
| **Message types** | `alert` |
| **Frequency** | Rare -- only for events with global significance |
| **Alert types** | `nuclear_launch`, `election_result`, `war_declared`, `peace_signed`, `regime_change`, `tech_breakthrough`, `chokepoint_blocked`, `chokepoint_opened` |
| **Example message** | |

```json
{
  "type": "alert",
  "channel": "sim:abc123:alerts",
  "payload": {
    "alert_type": "war_declared",
    "severity": "HIGH",
    "description": "Cathay has declared war on Formosa",
    "countries_involved": ["cathay", "formosa"],
    "round": 4,
    "timestamp": "2026-04-15T14:45:00Z"
  }
}
```

### `sim:{sim_id}:chat:{channel_id}`

| Property | Value |
|----------|-------|
| **Purpose** | Messaging channels for team coordination and AI participant meetings |
| **Subscribers** | Members of the channel (country teams, bilateral meeting participants) |
| **Channel ID patterns** | `team_{country_id}` (country team), `meeting_{meeting_id}` (ad-hoc meeting), `ai_meeting_{role_id}_{ai_role_id}` (AI participant meeting) |
| **Message types** | `chat_message` |
| **Frequency** | User-driven, real-time |
| **Auth rule** | JWT `role_id` must be in channel membership list |
| **Example message** | |

```json
{
  "type": "chat_message",
  "channel": "sim:abc123:chat:team_columbia",
  "payload": {
    "message_id": "msg_<ulid>",
    "sender_role_id": "pentagon",
    "content": "Naval deployment complete. 5 ships now in Pacific theater.",
    "timestamp": "2026-04-15T14:25:00Z"
  }
}
```

## 2.3 Channel Subscription Matrix

| User Type | world | country:{own} | role:{own} | facilitator | phase | alerts | chat:{own_channels} |
|-----------|:-----:|:-------------:|:----------:|:-----------:|:-----:|:------:|:-------------------:|
| Participant | Yes | Yes | Yes | No | Yes | Yes | Yes |
| Moderator | Yes | Yes (all) | Yes (all) | Yes | Yes | Yes | Yes (all, read-only) |
| Spectator | Yes | No | No | No | Yes | Yes | No |
| AI Agent | Yes | Yes | Yes | No | Yes | Yes | Yes |
| Admin | Yes | Yes (all) | Yes (all) | Yes | Yes | Yes | Yes (all) |

## 2.4 Client Reconnection Protocol

1. Client connects with JWT token. Server subscribes to channels based on token claims.
2. On disconnect, client retries with exponential backoff (1s, 2s, 4s, 8s, max 30s).
3. On reconnect, client sends `last_snapshot_version` for each channel.
4. Server replays missed events since that version.
5. If gap is too large (>100 events), server sends full state refresh instead.

---

# PART 3: MODULE INTERFACE CONTRACTS (C4)

## 3.1 World Model Engine

**Function:** `process_round(input) -> output`
**Mode:** BATCH (Phase B)
**Timing target:** < 5 minutes total (Pass 1 < 1s, Pass 2 < 30s, Pass 3 < 60s)
**Pass 2 dependencies:** Context Assembly Service (SEED_D9) provides methodology and prompt templates via `sim_config`; NOUS (SEED_D10) handles AI assessment, recommendation generation, and audit logging via `judgment_log`. See DET_F5 sections 2.11-2.13 for API contracts.

### Input

```json
{
  "round_num": 3,
  "world_state": {
    "_schema_version": "1.0",
    "round_num": 2,
    "countries": {
      "<country_id>": {
        "id": "string",
        "sim_name": "string",
        "regime_type": "string",
        "economic": {
          "gdp": "float",
          "gdp_growth_rate": "float",
          "sectors": {
            "resources": "float",
            "industry": "float",
            "services": "float",
            "technology": "float"
          },
          "tax_rate": "float",
          "treasury": "float",
          "inflation": "float",
          "debt_burden": "float",
          "oil_producer": "bool",
          "opec_member": "bool",
          "opec_production": "string",
          "formosa_dependency": "float",
          "social_spending_baseline": "float",
          "economic_state": "string",
          "momentum": "float (AI Pass 2 only -- not computed by deterministic engine)",
          "market_indexes": { "wall_street": "int", "europa": "int", "dragon": "int" },
          "starting_inflation": "float"
        },
        "military": {
          "ground": "int",
          "naval": "int",
          "tactical_air": "int",
          "strategic_missile": "int",
          "air_defense": "int",
          "production_costs": { "ground": "float", "naval": "float", "tactical_air": "float" },
          "production_capacity": { "ground": "int", "naval": "int", "tactical_air": "int" },
          "maintenance_cost_per_unit": "float",
          "strategic_missile_growth": "int",
          "mobilization_pool": "int"
        },
        "political": {
          "stability": "float",
          "political_support": "float",
          "war_tiredness": "float",
          "dem_rep_split": { "dem": "float", "rep": "float" },
          "regime_type": "string",
          "regime_status": "string"
        },
        "technology": {
          "nuclear_level": "int",
          "nuclear_rd_progress": "float",
          "ai_level": "int",
          "ai_rd_progress": "float"
        }
      }
    },
    "zones": { "<zone_id>": { "id": "string", "type": "string", "owner": "string", "theater": "string", "forces": {} } },
    "bilateral": {
      "tariffs": { "<imposer>": { "<target>": "int" } },
      "sanctions": { "<imposer>": { "<target>": "int" } }
    },
    "wars": [
      {
        "attacker": "string",
        "defender": "string",
        "theater": "string",
        "start_round": "int",
        "allies": { "attacker": ["string"], "defender": ["string"] },
        "occupied_zones": ["string"]
      }
    ],
    "oil_price": "float",
    "opec_production": { "<country_id>": "string" },
    "global_trade_volume_index": "float",
    "chokepoint_status": { "<chokepoint>": "string" },
    "treaties": [],
    "basing_rights": [],
    "roles": {},
    "nuclear_used_this_sim": "bool",
    "ground_blockades": {},
    "active_blockades": {},
    "rare_earth_restrictions": { "<country_id>": "int" },
    "formosa_blockade": "bool",
    "dollar_credibility": "float"
  },
  "country_actions": {
    "<country_id>": {
      "budget": {
        "social_allocation": "float",
        "military_allocation": "float",
        "technology_allocation": "float",
        "military_production": {
          "<unit_type>": { "coins": "float", "tier": "string" }
        },
        "tech_rd": { "nuclear": "float", "ai": "float" }
      },
      "tariffs": [{ "target": "string", "new_level": "int" }],
      "sanctions": [{ "target": "string", "new_level": "int" }],
      "military": [{ "action_type": "string", "target_zone": "string", "units": {} }],
      "diplomatic": [{ "action_type": "string", "content": "string" }]
    }
  },
  "event_log": ["<all events from Phase A>"]
}
```

### Output

```json
{
  "round_num": 3,
  "new_world_state": { "<full updated WorldState -- same schema as input>" },
  "events": [
    {
      "event_type": "engine.country_update",
      "actor_country_id": "<country_id>",
      "visibility": "COUNTRY",
      "payload": { "<per-country economic, military, political, tech deltas>" }
    }
  ],
  "combat_results": [
    {
      "attacker": "string",
      "defender": "string",
      "zone": "string",
      "attacker_units": {},
      "defender_units": {},
      "outcome": "attacker_wins | attacker_repelled | stalemate",
      "attacker_losses": {},
      "defender_losses": {},
      "zone_control_change": { "zone": "string", "old_owner": "string", "new_owner": "string" }
    }
  ],
  "transactions_executed": [
    { "transaction_id": "string", "type": "string", "parties": [], "state_changes": [] }
  ],
  "elections": {
    "<election_id>": {
      "winner": "string",
      "margin": "float",
      "effects": {}
    }
  },
  "narrative": "string (generated round briefing, 200-400 words)",
  "expert_panel": {
    "keynes": [{ "country": "string", "assessment": "string", "adjustment": {}, "confidence": "float" }],
    "clausewitz": [{ "country": "string", "assessment": "string", "adjustment": {}, "confidence": "float" }],
    "machiavelli": [{ "country": "string", "assessment": "string", "adjustment": {}, "confidence": "float" }],
    "applied": [{ "country": "string", "adjustment": "string", "source_votes": [] }],
    "rejected": []
  },
  "coherence_flags": [
    {
      "severity": "HIGH | MEDIUM | LOW",
      "description": "string",
      "auto_fixed": "bool",
      "country": "string",
      "field": "string",
      "old_value": "any",
      "new_value": "any"
    }
  ],
  "processing_metadata": {
    "pass_1_duration_ms": "int",
    "pass_2_duration_ms": "int",
    "pass_3_duration_ms": "int",
    "total_duration_ms": "int",
    "countries_processed": "int",
    "events_generated": "int"
  }
}
```

### Processing Steps (14 chained)

| Step | Input From | Output To | Touches |
|------|-----------|-----------|---------|
| 0 | `country_actions` | world_state | tariffs, sanctions, OPEC, rare earth, blockades |
| 1 | OPEC, sanctions, chokepoints, wars, demand | Step 2, 3, 13 | oil_price |
| 2 | oil_price, delta-only factors, sanctions/tariff coefficients | Step 3, 12, 13 | gdp, gdp_growth_rate |
| 3 | gdp, tax_rate, oil_revenue, debt, inflation | Step 4 | revenue |
| 4 | revenue, mandatory costs, player allocations | Step 5, 6, 7, 8 | treasury, social_spending, military_budget, tech_budget |
| 5 | military_budget, production_capacity, costs | N/A | unit counts |
| 6 | tech_budget, rare_earth, current_progress | N/A | nuclear_level/progress, ai_level/progress |
| 7 | money_printed, gdp | Step 9 | inflation |
| 8 | deficit | Step 9 | debt_burden |
| 9 | all economic indicators | Step 11.5, 12 | economic_state |
| 10 | ~~gdp_growth, economic_state, shocks~~ | ~~N/A~~ | ~~momentum~~ **AI Pass 2 only -- removed from deterministic engine** |
| 11 | ~~economic_states, trade_weights~~ | ~~Step 12~~ | ~~contagion effects on GDP~~ **Delegated to AI Pass 2 -- no formula-based contagion** |
| 11.5 | economic_state, component country health | Step 12 | **market_indexes** (3 regional: Wall Street, Europa, Dragon) |
| 12 | gdp_growth, social, war, sanctions, inflation, market_indexes | Step 13 | stability |
| 13 | gdp_growth, stability, casualties, crisis, oil | N/A | political_support |

---

## 3.2 Live Action Engine

**Function:** `process_action(input) -> output`
**Mode:** REAL-TIME (Phase A)
**Timing target:** < 2 seconds

### Input

```json
{
  "action_type": "ground_attack | naval_combat | blockade | air_strike | strategic_missile | nuclear_strike | naval_bombardment | arrest | fire_role | coup_attempt | assassination | sabotage | cyber_attack | disinformation | election_meddling | propaganda | protest | impeachment | mobilization_order | militia_call",
  "actor_role_id": "string",
  "actor_country_id": "string",
  "params": {
    "target_zone": "string (military actions)",
    "from_zone": "string (military actions)",
    "units": { "<unit_type>": "int" },
    "target_role_id": "string (political actions)",
    "target_country_id": "string (covert actions)",
    "target_type": "string (covert actions)",
    "coins_spent": "float (propaganda)",
    "secondary_conspirator_role_id": "string (coup)"
  },
  "current_state": { "<full WorldState JSON>" }
}
```

### Output

```json
{
  "success": "bool",
  "result": {
    "outcome": "string (action-specific result descriptor)",
    "attacker_losses": {},
    "defender_losses": {},
    "zone_control_change": { "zone": "string", "old_owner": "string", "new_owner": "string" },
    "target_new_status": "string (for role-affecting actions)",
    "detection": { "detected": "bool", "attribution": "string | null" },
    "effect": "string (for covert actions)",
    "impact_value": "float (for covert/political actions)"
  },
  "state_changes": [
    { "path": "string (dot-separated state path)", "old": "any", "new": "any" }
  ],
  "events": [
    { "<event objects following event envelope schema>" }
  ],
  "error": {
    "code": "string | null",
    "message": "string | null"
  }
}
```

### Validation Rules (checked before processing)

| Rule | Applies To | Error Code |
|------|-----------|------------|
| Actor role has required power | All actions | `AUTH_INSUFFICIENT_POWER` |
| Units available in from_zone | Military actions | `RESOURCE_NO_UNITS` |
| from_zone and target_zone are adjacent | Ground attack, naval combat | `VALIDATION_NOT_ADJACENT` |
| No attack on ally without war declaration | Military actions | `STATE_NO_WAR_DECLARED` |
| Authorization chain complete (e.g., nuclear requires HoS + military chief) | Nuclear, strategic missile | `AUTH_AUTHORIZATION_INCOMPLETE` |
| Cards remaining > 0 | Covert actions, assassination | `RESOURCE_NO_CARDS` |
| Target role is active | Arrest, fire, assassination | `STATE_TARGET_NOT_ACTIVE` |
| Current phase is A | All real-time actions | `STATE_WRONG_PHASE` |
| Round is not frozen | All actions | `STATE_ROUND_FROZEN` |

---

## 3.3 Transaction Engine

**Function:** `process_transaction(input) -> output`
**Mode:** REAL-TIME (Phase A)
**Timing target:** < 5 seconds

### Input

```json
{
  "transaction_type": "coin_transfer | arms_transfer | tech_transfer | basing_rights | treaty | agreement | org_creation | personal_investment | bribe",
  "proposer_role_id": "string",
  "proposer_country_id": "string",
  "counterparty_role_id": "string",
  "counterparty_country_id": "string",
  "details": {
    "from_country": "string",
    "to_country": "string",
    "amount": "float (for coin transfers)",
    "units": { "<unit_type>": "int (for arms transfers)" },
    "tech_transfer": { "domain": "string", "level": "int" },
    "basing_zone": "string (for basing rights)",
    "conditions": "string (free text terms)",
    "public": "bool (whether agreement is publicly visible)",
    "duration_rounds": "int | null (null = permanent)"
  },
  "current_state": { "<full WorldState JSON>" }
}
```

### Output (Proposal Stage)

```json
{
  "success": "bool",
  "transaction_id": "string",
  "requires_confirmation": true,
  "confirmation_token": "string",
  "expires_at": "ISO 8601",
  "validation": {
    "proposer_can_afford": "bool",
    "proposer_treasury": "float",
    "units_available": "bool",
    "legal": "bool"
  },
  "state_changes": [],
  "events": [
    { "event_type": "action.transaction_propose", "visibility": "ROLE" }
  ],
  "error": null
}
```

### Output (Execution Stage, after counterparty confirms)

```json
{
  "success": "bool",
  "requires_confirmation": false,
  "state_changes": [
    { "path": "string", "old": "any", "new": "any" }
  ],
  "events": [
    { "event_type": "action.transaction_confirm", "visibility": "COUNTRY" }
  ],
  "error": null
}
```

### Supported Transaction Types

| Type | Transfers | Visibility | Reversible |
|------|----------|------------|:----------:|
| `coin_transfer` | Treasury between countries | COUNTRY | No |
| `arms_transfer` | Military units between countries (1-round reduced effectiveness) | COUNTRY | No |
| `tech_transfer` | Technology sharing (replicable: receiver gains, sender keeps) | COUNTRY | No |
| `basing_rights` | Military basing permission | COUNTRY | Revocable |
| `treaty` | Recorded text agreement (not mechanically enforced) | PUBLIC or ROLE | No |
| `agreement` | Mechanically binding (subtypes: ceasefire, peace, trade, alliance) | PUBLIC or ROLE | No |
| `org_creation` | Create new international organization | PUBLIC | No |
| `personal_investment` | Role personal coins into country R&D | ROLE | No |
| `bribe` | Role-to-role covert payment | ROLE | No |

*Per DET_NAMING_CONVENTIONS 1.2. Deprecated names (transfer_coins, trade_deal, aid_package, personal_invest) must not be used.*

---

## 3.4 AI Participant Module

**Function:** `generate_decisions(input) -> output`
**Mode:** Called once per round per AI agent during Phase A
**Timing target:** < 30 seconds per agent

### Input

```json
{
  "role_id": "string",
  "role_brief": "string (full prose brief from role_briefs/<ROLE_ID>.md)",
  "character_name": "string",
  "country_id": "string",
  "visible_state": {
    "own_country": {
      "economic": { "gdp": "float", "treasury": "float", "inflation": "float", "debt_burden": "float", "economic_state": "string", "momentum": "float (AI Pass 2 only)", "market_indexes": { "wall_street": "int", "europa": "int", "dragon": "int" }, "revenue_last_round": "float" },
      "military": { "ground": "int", "naval": "int", "tactical_air": "int", "strategic_missile": "int", "air_defense": "int", "total": "int", "production_capacity": {} },
      "political": { "stability": "float", "political_support": "float", "war_tiredness": "float", "regime_status": "string" },
      "technology": { "nuclear_level": "int", "nuclear_rd_progress": "float", "ai_level": "int", "ai_rd_progress": "float" }
    },
    "world": {
      "oil_price": "float",
      "active_wars": [{ "attacker": "string", "defender": "string", "theater": "string" }],
      "chokepoint_status": { "<chokepoint>": "string" },
      "public_economic_tiers": { "<country_id>": "small | medium | large | major" },
      "public_military_tiers": { "<country_id>": "weak | moderate | strong | superpower" }
    },
    "map": {
      "own_forces": { "<zone_id>": { "<unit_type>": "int" } },
      "visible_forces": { "<zone_id>": { "<country_id>": { "<unit_type>": "int" } } }
    },
    "relationships": { "<country_id>": "allied | friendly | neutral | tense | hostile | at_war" },
    "bilateral": {
      "tariffs_imposed_by_us": { "<country_id>": "int" },
      "tariffs_imposed_on_us": { "<country_id>": "int" },
      "sanctions_imposed_by_us": { "<country_id>": "int" },
      "sanctions_imposed_on_us": { "<country_id>": "int" }
    }
  },
  "available_actions": [
    {
      "action_type": "string",
      "constraints": {},
      "cost": "float | null"
    }
  ],
  "round_context": {
    "round_num": "int",
    "phase": "A",
    "time_remaining_seconds": "int",
    "recent_events": [{ "summary": "string", "round": "int" }],
    "scheduled_events_this_round": [{ "type": "string", "description": "string" }]
  },
  "objectives": ["string"],
  "ticking_clock": "string",
  "conversation_history": [
    {
      "round": "int",
      "counterparty_role_id": "string",
      "summary": "string"
    }
  ],
  "previous_decisions": [
    {
      "round": "int",
      "actions": [{ "action_type": "string", "summary": "string" }]
    }
  ]
}
```

### Output

```json
{
  "actions": [
    {
      "action_type": "string",
      "params": {},
      "priority": "int (1 = highest)",
      "reasoning": "string (1-2 sentences)"
    }
  ],
  "negotiations": [
    {
      "target_role_id": "string",
      "proposal": "string (what to propose in meeting)",
      "reasoning": "string",
      "priority": "int"
    }
  ],
  "statements": [
    {
      "audience": "public | organization:<org_id>",
      "content": "string (speech text, in character voice)",
      "timing": "early | mid | late (when in phase to deliver)"
    }
  ],
  "deployments": [
    {
      "unit_type": "string",
      "count": "int",
      "from_zone": "string",
      "to_zone": "string"
    }
  ],
  "internal_reasoning": "string (MODERATOR-ONLY: 2-5 sentences explaining strategic thinking)"
}
```

**Constraints on AI output:**
- AI actions go through the same validation pipeline as human actions.
- AI output is logged as events with `actor_role_id = <role_id>` (not "ai").
- `internal_reasoning` is never shown to other participants.
- AI agent must not exceed available resources (treasury, units, cards).
- AI agent sees only data matching its visibility level (same as human in that role).

---

## 3.5 Argus (AI Assistant)

**Function:** `respond_to_participant(input) -> output`
**Mode:** On-demand, anytime during Phase A or debrief
**Timing target:** < 5 seconds for text, < 8 seconds for voice

### Input

```json
{
  "participant_user_id": "string",
  "participant_role_id": "string",
  "participant_country_id": "string",
  "argus_phase": "INTRO | MID | OUTRO",
  "question": "string (participant's message, text or transcribed voice)",
  "conversation_history": [
    {
      "role": "participant | argus",
      "content": "string",
      "timestamp": "ISO 8601"
    }
  ],
  "role_context": {
    "character_name": "string",
    "title": "string",
    "objectives": ["string"],
    "ticking_clock": "string",
    "powers": ["string"]
  },
  "visible_world_state": {
    "own_country_summary": "string (generated from country state)",
    "world_summary": "string (generated from public state)",
    "recent_events_summary": "string"
  },
  "current_round": "int",
  "current_phase": "A | B",
  "participant_action_history": [
    { "round": "int", "action_type": "string", "summary": "string" }
  ]
}
```

### Output

```json
{
  "response_text": "string (Argus response in mentoring voice)",
  "voice_audio_url": "string | null (URL to generated audio, null if text-only mode)",
  "voice_duration_seconds": "float | null",
  "suggested_actions": [
    {
      "action_type": "string",
      "rationale": "string",
      "priority": "string (consider | recommended | urgent)"
    }
  ],
  "reflection_prompt": "string | null (only in OUTRO phase -- question for self-reflection)",
  "metadata": {
    "model_id": "string",
    "processing_time_ms": "int",
    "tokens_used": { "input": "int", "output": "int" },
    "tts_model": "string | null"
  }
}
```

**Argus boundaries:**
- Cannot send messages to other participants on the user's behalf.
- Cannot reveal data above the participant's visibility level.
- Cannot execute actions -- only suggest.
- In INTRO phase: focuses on goal-setting and role understanding.
- In MID phase: provides strategic advice, rules clarification, situational awareness.
- In OUTRO phase: facilitates reflection on decisions and outcomes.
- Memory persists across all conversations with the same participant within the SIM run.

---

*This document defines the complete system contracts for TTT: event schemas (C1), real-time channel map (C2), module interface contracts (C4), orchestration (C5), and concurrency rules (C6). For the OpenAPI specification, see DET_C3_API_SPEC.yaml.*

---

# PART 4: MODULE ORCHESTRATION (C5)

## 4.1 Round State Machine

Every round follows this formal sequence. Transitions are managed by the orchestrator; no module may call another out of sequence.

```
┌──────────────────────────────────────────────────────────┐
│                    ROUND N LIFECYCLE                      │
│                                                          │
│  STATE 1: PHASE_A_ACTIVE                                 │
│  ┌────────────────────────────────────────────────────┐  │
│  │ Duration: configurable (60-180s unmanned,          │  │
│  │          60-120min real-time)                       │  │
│  │                                                    │  │
│  │ ACTIVE MODULES:                                    │  │
│  │  • AI Participant Module (active loop, parallel)   │  │
│  │  • Live Action Engine (on demand, per action)      │  │
│  │  • Transaction Engine (on demand, per transaction) │  │
│  │                                                    │  │
│  │ HUMAN/AI ACTIONS: submitted any time               │  │
│  │  → Validated by Edge Function / Action Framework   │  │
│  │  → Resolved by Live Action or Transaction Engine   │  │
│  │  → Events logged immediately                       │  │
│  │  → Real-time broadcast to subscribers              │  │
│  │                                                    │  │
│  │ AI PARTICIPANT LOOP:                               │  │
│  │  Every N seconds: check events → decide → act      │  │
│  │  Conversations: bilateral, 8 turns, between agents │  │
│  │  Memory updates: after each conversation/action    │  │
│  └────────────────────────────────────────────────────┘  │
│           │ (timer expires OR moderator advances)        │
│           ▼                                              │
│  STATE 2: PHASE_A_SUBMISSION                             │
│  ┌────────────────────────────────────────────────────┐  │
│  │ Duration: 30 seconds (automatic collection)        │  │
│  │                                                    │  │
│  │ COLLECT MANDATORY INPUTS from all HoS:             │  │
│  │  • budget_submit (social, military, tech)          │  │
│  │  • tariff_set (per target country)                 │  │
│  │  • sanction_set (per target country)               │  │
│  │  • opec_production (OPEC members)                  │  │
│  │                                                    │  │
│  │ AI agents: derive from current Block 4 strategy    │  │
│  │ Human: submit via UI (or defaults applied)         │  │
│  └────────────────────────────────────────────────────┘  │
│           │                                              │
│           ▼                                              │
│  STATE 3: PHASE_B_PROCESSING                             │
│  ┌────────────────────────────────────────────────────┐  │
│  │ Duration: < 5 minutes                              │  │
│  │                                                    │  │
│  │ SEQUENTIAL EXECUTION (no parallelism):             │  │
│  │  1. World Model Engine Pass 1 (deterministic)      │  │
│  │     Oil → GDP → Revenue → Budget → Production →    │  │
│  │     Tech → Inflation → Debt → Market Indexes →     │  │
│  │     Stability → Support                            │  │
│  │                                                    │  │
│  │  2. NOUS Pass 2 (AI judgment)                      │  │
│  │     Context assembled → LLM call → adjustments     │  │
│  │     Mode: automatic (unmanned) or manual review    │  │
│  │                                                    │  │
│  │  3. Pass 3 (coherence + narrative)                 │  │
│  │     Plausibility check → round summary             │  │
│  │                                                    │  │
│  │  4. Elections (if scheduled this round)             │  │
│  │  5. Revolution checks                              │  │
│  │  6. Health events                                  │  │
│  │                                                    │  │
│  │ OUTPUT: New world state snapshot + events           │  │
│  └────────────────────────────────────────────────────┘  │
│           │                                              │
│           ▼                                              │
│  STATE 4: RESULTS_BROADCAST                              │
│  ┌────────────────────────────────────────────────────┐  │
│  │ Duration: immediate                                │  │
│  │                                                    │  │
│  │ • Snapshot persisted (immutable)                    │  │
│  │ • Events broadcast via real-time channels           │  │
│  │ • Each recipient sees visibility-scoped results     │  │
│  │ • AI agents: Priority 1 reflection (memory update)  │  │
│  └────────────────────────────────────────────────────┘  │
│           │                                              │
│           ▼                                              │
│  STATE 5: PHASE_C_DEPLOYMENT                             │
│  ┌────────────────────────────────────────────────────┐  │
│  │ Duration: 60 seconds (unmanned) / 5 min (real-time)│  │
│  │                                                    │  │
│  │ • HoS deploys new/moved units to zones             │  │
│  │ • Reserve movements executed                        │  │
│  │ • No combat, no negotiations                        │  │
│  └────────────────────────────────────────────────────┘  │
│           │                                              │
│           ▼                                              │
│  → ROUND N+1 (loop to STATE 1)                          │
│    OR                                                    │
│  → GAME_END (if round_num == max_rounds)                 │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

## 4.2 Module Call Sequence (Phase B — formal)

No module may be invoked out of this order during Phase B:

| Step | Module | Input | Output | Depends on |
|:----:|--------|-------|--------|-----------|
| 1 | **World Model Engine Pass 1** | world_state + actions + events | updated state + formula results | All Phase A events collected |
| 2 | **NOUS Pass 2** | Pass 1 output + methodology | judgment adjustments | Pass 1 complete |
| 3 | **Apply NOUS adjustments** | judgment result | modified state | Pass 2 complete |
| 4 | **Elections** (if scheduled) | political state | election results | Pass 2 applied |
| 5 | **Revolution / health checks** | stability + support | regime events | Elections resolved |
| 6 | **Pass 3 Narrative** | full round state | round summary | All above complete |
| 7 | **Persist snapshot** | final state | immutable snapshot | Narrative generated |
| 8 | **Broadcast results** | events + state deltas | WebSocket messages | Snapshot persisted |

**Failure rule:** If any step fails, the round is marked FAILED. No partial results are committed. The moderator must intervene to retry or skip.

## 4.3 Module Call Sequence (Phase A — concurrent)

During Phase A, multiple modules operate **concurrently**:

```
AI Participant Loop ──→ submits action ──→ Action Framework
                                               │
Human UI ─────────────→ submits action ──→ Action Framework
                                               │
                                               ▼
                                    ┌─ ROUTE BY TYPE ──┐
                                    │                   │
                                    ▼                   ▼
                            Live Action Engine    Transaction Engine
                            (combat, blockade)    (bilateral deals)
                                    │                   │
                                    ▼                   ▼
                            Events generated      Events generated
                                    │                   │
                                    └─────┬─────────────┘
                                          ▼
                                    Event Log + Broadcast
```

All actions go through the same **Action Framework** regardless of source (human or AI). The Action Framework validates authorization, resources, and timing before routing to the appropriate engine.

---

# PART 5: AI PARTICIPANT ABSTRACT INTERFACE (C6)

## 5.1 Purpose

The AI Participant Module has a **stable abstract interface** that decouples the module's capabilities from its implementation. Multiple implementations can exist behind this interface:

- **Implementation A (KING-style):** 4-block cognitive model with context caching, explicit memory management, Gemini/Claude LLM calls
- **Implementation B (Anthropic persistent):** Long-running conversation with tool use, native memory, Claude Agent SDK
- **Future implementations:** Fine-tuned models, hybrid approaches

All implementations MUST conform to this interface. The test interface and the engine orchestrator interact with the AI Participant through this contract only.

## 5.2 Abstract Interface

```
AIParticipant
│
├── initialize(role_id, sim_config, world_state) → ParticipantState
│     Create and configure the agent. Load role data, generate identity.
│     Called once per SIM run.
│
├── start_round(round_num, world_state_visible, events_since_last) → void
│     Begin a new round. Update situational awareness.
│     Called at STATE 1 (PHASE_A_ACTIVE) entry.
│
├── decide_action(time_remaining, new_events) → ActionDecision
│     Proactive decision: what to do RIGHT NOW?
│     Returns: action to take, or WAIT.
│     Called repeatedly during active loop.
│     ActionDecision: {action_type, details, reasoning} | WAIT
│
├── react_to_event(event) → ActionDecision | null
│     Handle an incoming event (proposal, combat result, message).
│     Returns: reaction action, or null (acknowledge only).
│     Called when Priority 1 event arrives.
│
├── generate_conversation_message(conversation_context) → Message
│     Produce next message in a conversation.
│     Called during bilateral/multi-party conversations.
│     Message: {text, proposals_made, end_conversation}
│
├── evaluate_proposal(proposal, counterpart_context) → ProposalResponse
│     Accept, reject, or counter a transaction/deal proposal.
│     ProposalResponse: {decision: accept|reject|counter, terms?, reasoning}
│
├── submit_mandatory_inputs(round_context) → MandatoryInputs
│     Produce round-end mandatory decisions.
│     Called at STATE 2 (PHASE_A_SUBMISSION).
│     MandatoryInputs: {budget, tariffs, sanctions, opec, deployments}
│
├── reflect_on_round(round_results) → void
│     Update internal state after round results arrive.
│     Called at STATE 4 (RESULTS_BROADCAST).
│
├── get_cognitive_state() → CognitiveState
│     Return current cognitive blocks (for inspection/debugging).
│     CognitiveState: {block1_rules, block2_identity, block3_memory, block4_goals, version}
│
├── get_state_history() → list[CognitiveState]
│     Return all past versions of cognitive state.
│     For debugging and analysis.
│
└── chat(message, inspector_context) → ChatResponse
      Debug interface: human talks to the agent outside the game.
      The agent responds in character with full cognitive context.
      ChatResponse: {text, blocks_referenced}
```

## 5.3 Data Contracts

### ActionDecision

```json
{
  "action_type": "string (from action catalog, or 'WAIT')",
  "details": {
    // Action-specific parameters matching DET_C1 Part 1.2 event payloads
  },
  "reasoning": "string (1-2 sentences, MODERATOR-only)",
  "priority": "int (1=highest)"
}
```

### MandatoryInputs

```json
{
  "budget": {
    "social_pct": "float (0.5-1.5, multiplier of baseline)",
    "military_coins": "float",
    "tech_coins": "float"
  },
  "tariffs": { "<country_id>": "int (0-3)" },
  "sanctions": { "<country_id>": "int (0-3)" },
  "opec_production": "string (min|low|normal|high|max) | null",
  "deployments": [
    { "unit_type": "string", "count": "int", "to_zone": "string" }
  ]
}
```

### CognitiveState (Implementation A — 4-block model)

```json
{
  "version": "int (incremented on each update)",
  "timestamp": "ISO 8601",
  "block1_rules": "string (~3K tokens, cached)",
  "block2_identity": "string (~500 tokens, cached, rarely updated)",
  "block3_memory": {
    "immediate": "string (last event)",
    "round_history": [{ "round": "int", "summary": "string" }],
    "strategic": "string (persistent key facts)",
    "relationships": { "<role_id>": "float (-1 to +1)" }
  },
  "block4_goals": {
    "objectives": [{ "name": "string", "urgency": "float", "status": "string" }],
    "current_strategy": "string",
    "contingencies": "string"
  }
}
```

### CognitiveState (Implementation B — Anthropic persistent agent)

```json
{
  "version": "int",
  "timestamp": "ISO 8601",
  "conversation_id": "string (Anthropic conversation reference)",
  "system_prompt": "string (identity + rules)",
  "message_count": "int",
  "last_summary": "string (periodic self-summary)",
  "tools_available": ["string (registered tool names)"]
}
```

Both implementations expose the same `get_cognitive_state()` interface. The test interface renders the appropriate view based on implementation type.

### 5.6 Cognitive State Persistence

Cognitive blocks are persisted in the `ai_context` table (DET_B1). Each update creates a new versioned row with `is_current=true` (previous version set to `is_current=false`). This provides:
- Full audit trail of cognitive evolution
- Version navigation for debugging (test interface)
- Rollback capability if needed
- Cross-session persistence for long-running SIMs

AI participant prompts (identity generation, conversation behavior, reflection prompts, intent note generation, meeting decisions) are stored in `sim_config` with `category='prompt_template'`. This allows moderator editing between rounds without code deployment.

## 5.4 Action Validation Contract

Every action produced by `decide_action()` or `submit_mandatory_inputs()` passes through the **Action Framework** before execution:

```
AIParticipant.decide_action()
    │
    ▼
Action Framework validates:
    1. Authorization: role has power for this action_type
    2. Resources: treasury/units/intel_pool sufficient
    3. Timing: action allowed in current phase
    4. Rules: action legal given current state
    5. Co-signature: multi-role authorization if required
    │
    ├── VALID → route to Live Action / Transaction Engine
    │           → execute → events generated → broadcast
    │
    └── INVALID → log rejection → notify agent
                  → agent.react_to_event({type: "action_rejected", reason})
```

## 5.5 Conversation Protocol

Conversations between AI participants (or AI ↔ human) use this protocol:

```
Initiator calls: decide_action() → {action_type: "request_conversation", target_role_id, intent}
    │
    ▼
Action Framework:
    1. Check initiator is IDLE
    2. Check target is IDLE
    3. Create conversation record
    │
    ▼
Conversation Loop (max 8 turns per side):
    Turn 1: initiator.generate_conversation_message(context) → message
    Turn 2: responder.generate_conversation_message(context + msg1) → message
    Turn 3: initiator.generate_conversation_message(context + msg1 + msg2) → message
    ...
    End: either side returns {end_conversation: true} OR max turns reached
    │
    ▼
Post-conversation:
    1. Transcript logged (visibility: ROLE for participants, MODERATOR for all)
    2. Both agents: reflect immediately (Priority 1 memory update)
    3. Any proposals made → logged as pending transactions
    4. Both agents return to IDLE status
```

---

# PART 6: CONCURRENCY & CONSISTENCY RULES (C7)

## 6.1 Agent Concurrency During Phase A

Multiple AI agents operate **simultaneously** during Phase A. Rules:

| Rule | Description |
|------|------------|
| **Agent status lock** | Each agent has status: IDLE, DECIDING, ACTING, BUSY, REFLECTING. Only IDLE agents are polled in the active loop. |
| **Conversation exclusivity** | An agent in a conversation (BUSY) cannot start another or take other actions until the conversation completes. |
| **Action serialization per country** | Actions from the same country are serialized (processed one at a time). Actions from different countries can be parallel. |
| **State read-then-act** | Agent reads state at decision time. If state changes between read and action execution, the Action Framework re-validates. |
| **Event ordering** | Events within a round are ordered by timestamp. If two events have identical timestamps, country_id is used as tiebreaker. |

## 6.2 Optimistic Concurrency

The system uses **optimistic concurrency control** via `snapshot_version`:

1. Agent reads state at version V
2. Agent decides action based on version V state
3. Action submitted with `snapshot_version: V`
4. Action Framework checks: is current version still V?
   - If yes: execute, increment to V+1
   - If no: re-validate action against current version
     - If still valid: execute
     - If invalid (e.g., unit no longer exists): reject, notify agent

## 6.3 Conversation Concurrency

Two agents cannot be in the same conversation with a third simultaneously:

```
Agent A requests conversation with Agent C → starts (both BUSY)
Agent B requests conversation with Agent C → QUEUED (C is BUSY)
Agent A ↔ C conversation ends → both return to IDLE
Agent B ↔ C conversation starts (if B still wants it)
```

Queued requests expire if not fulfilled within the round.

## 6.4 Transaction Atomicity

Transactions are **atomic** at the database level:

1. Proposer creates pending transaction (state: PROPOSED)
2. Counterpart evaluates → accepts (state: ACCEPTED)
3. Execution: single database transaction updates both parties' state
4. If execution fails: transaction rolled back, both parties notified

No partial execution. Either both sides' state changes, or neither does.

## 6.5 Phase Transition Safety

When Phase A ends:
1. All active conversations are force-ended (transcripts saved)
2. All pending actions in queue are canceled
3. All agents set to IDLE
4. Mandatory inputs collected
5. Only THEN does Phase B begin

No action from Phase A can "leak" into Phase B processing.

---

## CHANGELOG (v1.1, 2026-03-30)

Fixes applied per DET_VALIDATION_LEVEL1 + DET_VALIDATION_LEVEL3 findings:

- **[HIGH] Standardized field names:** Event envelope `round` renamed to `round_num`. `event_id` format explicitly documented as ULID. All field names now reference DET_NAMING_CONVENTIONS.md as authority.
- **[HIGH] Transaction type enum aligned:** Module contract 3.3 (Transaction Engine) updated from (transfer_coins, trade_deal, basing_rights, aid_package, personal_invest, bribe) to canonical engine names (coin_transfer, arms_transfer, tech_transfer, basing_rights, treaty, agreement, org_creation, personal_investment, bribe). Per DET_NAMING_CONVENTIONS 1.2.
- **[MEDIUM] Live Action Engine contract expanded:** Module contract 3.2 action_type list now includes `impeachment`, `mobilization_order`, `militia_call`.
- **[MEDIUM] Event type mapping:** Formal mapping from engine internal action_type to C1 event_type is documented in DET_NAMING_CONVENTIONS 1.3 (single source of truth).
- **[LOW] Naming convention reference:** Header updated to reference DET_NAMING_CONVENTIONS.md as naming authority.

## CHANGELOG (v1.3, 2026-04-04)

- **[HIGH] PART 4 added: Module Orchestration (C5).** Formal round state machine. Phase B module call sequence formalized (7 steps, failure rule). Phase A concurrent module operation documented.
- **[HIGH] PART 5 added: AI Participant Abstract Interface (C6).** Implementation-agnostic contract that both KING-style and Anthropic modules must implement. 10 methods defined (initialize, decide_action, react_to_event, generate_conversation_message, evaluate_proposal, submit_mandatory_inputs, reflect_on_round, get_cognitive_state, get_state_history, chat). Data contracts for ActionDecision, MandatoryInputs, CognitiveState (both implementations).
- **[HIGH] PART 6 added: Concurrency & Consistency Rules (C7).** Agent status lifecycle, conversation exclusivity, action serialization per country, optimistic concurrency via snapshot_version, transaction atomicity, phase transition safety.
- **[MEDIUM] Action validation contract added to Part 5.** 5-step validation (authorization, resources, timing, rules, co-signature) with rejection flow.
- **[MEDIUM] Conversation protocol formalized in Part 5.** Initiation → turn loop → post-conversation reflection + transaction logging.

Fixes applied per DET_VALIDATION_LEVEL1 + DET_VALIDATION_LEVEL3 findings:

- **[HIGH] Standardized field names:** Event envelope `round` renamed to `round_num`. `event_id` format explicitly documented as ULID. All field names now reference DET_NAMING_CONVENTIONS.md as authority.
- **[HIGH] Transaction type enum aligned:** Module contract 3.3 (Transaction Engine) updated from (transfer_coins, trade_deal, basing_rights, aid_package, personal_invest, bribe) to canonical engine names (coin_transfer, arms_transfer, tech_transfer, basing_rights, treaty, agreement, org_creation, personal_investment, bribe). Per DET_NAMING_CONVENTIONS 1.2.
- **[MEDIUM] Live Action Engine contract expanded:** Module contract 3.2 action_type list now includes `impeachment`, `mobilization_order`, `militia_call`.
- **[MEDIUM] Event type mapping:** Formal mapping from engine internal action_type to C1 event_type is documented in DET_NAMING_CONVENTIONS 1.3 (single source of truth).
- **[LOW] Naming convention reference:** Header updated to reference DET_NAMING_CONVENTIONS.md as naming authority.
