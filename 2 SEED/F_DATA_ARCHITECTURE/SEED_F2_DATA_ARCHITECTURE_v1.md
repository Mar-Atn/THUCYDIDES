# TTT Data Architecture
## Foundation Specification — Everything Builds on This

**Version:** 1.0 | **Date:** 2026-03-28
**Status:** SEED Design (pre-implementation)
**Cross-references:** [F1 Data Schema](SEED_F1_DATA_SCHEMA_v1.md) | [F3 Data Flows](SEED_F3_DATA_FLOWS_v1.md) | [F4 API Contracts](SEED_F4_API_CONTRACTS_v1.md) | [D8 Engine Formulas](../D_ENGINES/SEED_D8_ENGINE_FORMULAS_v1.md)

---

# PART 1: DESIGN PRINCIPLES

## Principle 1: Store FACTS, Derive ASSESSMENTS

Every variable in the system falls into one of four categories:

| Category | Definition | Storage | Examples |
|----------|-----------|---------|----------|
| **CORE** | Facts that cannot be computed from other data. Represent physical reality, account balances, or accumulated state that requires full history to reconstruct. | Persisted in state snapshots and database. | GDP, treasury, inflation, unit counts, stability, treaties, personal_coins |
| **DERIVED** | Assessments computed deterministically from CORE variables and/or history. Given the same inputs, always produce the same output. | Never stored. Recomputed on demand or once per round. | economic_state, momentum, market_index, crisis_rounds, dollar_credibility |
| **INTERMEDIATE** | Calculation artifacts used within a single engine step. Have no meaning outside their computation context. | Never stored. Exist only in memory during processing. | money_printed_this_round, raw_growth, deficit, revenue |
| **CONFIG** | Constants and starting values. Set once before round 1. Never change during play. | Stored in CSV seed data and/or hardcoded constants. | starting_inflation, base_growth_rate, production_costs, thresholds |

**The rule:** If a variable CAN be derived, it MUST be derived. No exceptions. This prevents state drift, eliminates reconciliation bugs, and makes the event log the single behavioral record.

## Principle 2: Event Sourcing

Every action and state change is logged as an EVENT with timestamp, actor, action, and result. The event log is append-only. Current state can be reconstructed from initial state + event replay.

```
State(round N) = InitialState + replay(Events[round 0..N])
```

This gives us:
- **Auditability.** Every state change has a traceable cause.
- **Replay.** Any round can be reconstructed for debugging or analysis.
- **Analytics pipeline.** The event log IS the behavioral data that feeds post-SIM research.
- **Undo safety.** We never need undo -- we replay from a known-good snapshot.

## Principle 3: Information Layers

Every data point has a visibility level. The system enforces four tiers:

| Level | Who Sees It | Examples |
|-------|------------|---------|
| **PUBLIC** | All participants, spectators, moderator | Oil price, map positions (own + visible), public statements, war declarations, OPEC decisions |
| **COUNTRY** | Country team members + moderator | Own GDP, treasury, stability, political support, inflation, military totals, budget |
| **ROLE** | Specific role holder + moderator | Personal coins, intelligence reports, covert op results, role-specific artefacts |
| **MODERATOR** | Moderator/facilitator only | AI expert panel adjustments, coherence flags, exact values for all countries, internal engine diagnostics |

Information asymmetry is a core gameplay mechanic. Participants should make decisions with incomplete information, just as real-world leaders do. The data architecture must enforce these boundaries at the API layer, not rely on UI hiding.

## Principle 4: Immutable History

Past rounds are FROZEN. No retroactive changes. Each round produces a state snapshot that is immutable once the next round begins.

```
Snapshot(round 3) -- once round 4 starts, this is permanent.
No engine pass, no moderator override, no bug fix can alter it.
Corrections are logged as new events in the current round.
```

This means:
- Round snapshots serve as checkpoints for replay.
- Derived values for past rounds are recomputed from frozen snapshots, not stored.
- Moderator corrections are applied as "adjustment events" in the current round, not edits to past data.

## Principle 5: Single Source of Truth

Each variable has ONE canonical location. No duplication between CSVs, engine state, and web app database.

| Phase | Canonical Source | Consumers |
|-------|-----------------|-----------|
| **Pre-SIM setup** | CSV files in `data/` | Engine loader, validation scripts, future Supabase import |
| **During SIM (SEED/testing)** | JSON state snapshots | Engine, test harness, analysis scripts |
| **During SIM (BUILD/production)** | Supabase database | Web app, engine, AI agents, moderator dashboard |
| **Post-SIM analysis** | Event log + final snapshot | Research analytics, papers, after-action review |

The CSV-to-JSON-to-database pipeline is one-directional. CSVs are never updated from engine output. The engine reads state, computes new state, writes a new snapshot.

---

# PART 2: VARIABLE CLASSIFICATION

## Complete Audit of `world_state.py`

Every variable in the current `WorldState` class, classified against the principles above.

### Global State Variables

| Variable | Type | Store? | Justification |
|----------|------|:------:|---------------|
| `round_num` | CORE | Yes | Current round counter. Fundamental to all processing. |
| `oil_price` | CORE | Yes | Global commodity price. Output of Step 1 with stochastic noise -- cannot be recomputed identically without random seed. |
| `oil_price_index` | DERIVED | No | `= oil_price / 80 * 100`. Trivial derivation from oil_price. |
| `global_trade_volume_index` | CORE | Yes | Accumulated global trade state. Modified by multiple disruptions. |
| `nuclear_used_this_sim` | CORE | Yes | Binary flag. Once set, never reverts. Affects all subsequent processing. |
| `formosa_blockade` | CORE | Yes | Active blockade state. Set/unset by live action engine. |
| `formosa_resolved` | DERIVED | No | Check event log for `formosa_resolution` event. Derive from history. |
| `dollar_credibility` | CORE | Yes | Accumulated result of Columbia money printing. Requires full printing history to reconstruct. Storing is cheaper than replay. |
| `oil_above_150_rounds` | DERIVED | No | Count consecutive rounds where `oil_price > 150` from oil price history in snapshots. |

### Per-Country: Economic

| Variable | Type | Store? | Justification |
|----------|------|:------:|---------------|
| `gdp` | CORE | Yes | Fundamental economic fact. Updated each round by Step 2. |
| `gdp_growth_rate` | INTERMEDIATE | No | Calculated fresh each round in Step 2. Stored only in round snapshot as a convenience but NOT in canonical state. |
| `sectors` (resources, industry, services, technology) | CONFIG | Yes | Starting structural percentages. Set from CSV. Could change via future mechanics (structural reform) but currently static. |
| `tax_rate` | CONFIG | Yes | Set from CSV. Player-adjustable in future iterations. |
| `treasury` | CORE | Yes | Account balance. Running total of surpluses and deficits. |
| `inflation` | CORE | Yes | Monetary state. Changes via money printing and natural decay. |
| `trade_balance` | CONFIG | Yes | Starting value. Not currently updated by engine (placeholder for future). |
| `oil_producer` | CONFIG | Yes | Structural flag. Does not change. |
| `opec_member` | CONFIG | Yes | Structural flag. Does not change. |
| `opec_production` | CORE | Yes | OPEC member production decision. Changed by player action. |
| `formosa_dependency` | CONFIG | Yes | Structural dependency. Set from CSV. |
| `debt_burden` | CORE | Yes | Accumulated debt service. Grows with deficits, never auto-decreases. Full history needed to reconstruct. |
| `social_spending_baseline` | CONFIG | Yes | Structural parameter. Set from CSV. |
| `oil_revenue` | INTERMEDIATE | No | Calculated in Step 1, consumed in Step 3. Never stored between rounds. |
| `inflation_revenue_erosion` | INTERMEDIATE | No | Calculated in Step 3. Never stored. |
| `economic_state` | DERIVED | No | Deterministic function of oil_price, inflation, GDP growth, treasury, stability, formosa disruption. Recompute from Step 9 triggers each round. |
| `momentum` | CORE | Yes | Accumulated confidence. While theoretically derivable from full GDP/event history, the asymmetric build/crash rules and clamping make replay fragile. Storing is correct. |
| `crisis_rounds` | DERIVED | No | Count consecutive rounds where `economic_state in (crisis, collapse)`. Derive from economic_state history in snapshots. |
| `recovery_rounds` | DERIVED | No | Count rounds since leaving crisis. Derive from economic_state history. |
| `sanctions_rounds` | DERIVED | No | Count consecutive rounds under L2+ sanctions. Derive from sanctions history in event log. |
| `formosa_disruption_rounds` | DERIVED | No | Count consecutive rounds of semiconductor disruption. Derive from blockade events in event log. |
| `market_index` | DERIVED | No | Deterministic function of GDP growth, economic_state, stability, inflation, oil_price, partner indices. Recompute each round. |
| `starting_inflation` | CONFIG | Yes | Baseline for inflation delta calculations. Set once from CSV, never changes. |
| Flat sector aliases (`sector_resources`, etc.) | DUPLICATE | No | Exact copies of `sectors.*`. Remove -- use `sectors` dict only. |

### Per-Country: Military

| Variable | Type | Store? | Justification |
|----------|------|:------:|---------------|
| `ground` | CORE | Yes | Unit count. Changes via production and combat. |
| `naval` | CORE | Yes | Unit count. |
| `tactical_air` | CORE | Yes | Unit count. |
| `strategic_missiles` | CORE | Yes | Unit count. Auto-grows for Cathay. |
| `air_defense` | CORE | Yes | Unit count. Non-producible. |
| `production_costs` (per type) | CONFIG | Yes | Set from CSV. |
| `production_capacity` (per type) | CONFIG | Yes | Set from CSV. |
| `maintenance_cost_per_unit` | CONFIG | Yes | Set from CSV. |
| `strategic_missile_growth` | CONFIG | Yes | Auto-production rate. Cathay-specific. |
| `mobilization_pool` | CORE | Yes | Reserved for future mechanic. Currently 0. |

### Per-Country: Political

| Variable | Type | Store? | Justification |
|----------|------|:------:|---------------|
| `stability` | CORE | Yes | Political state. Too many inputs to re-derive efficiently (GDP, social spending, war, sanctions, inflation, crisis state, elections, covert ops). |
| `political_support` | CORE | Yes | Public approval. Same complexity as stability. |
| `dem_rep_split` | CORE | Yes | Columbia-specific partisan split. Changes via election results. |
| `war_tiredness` | CORE | Yes | Accumulated fatigue. Grows each round at war. Requires war duration history. |
| `regime_type` | CONFIG | Yes | Structural. Could change via revolution event but starts from CSV. |
| `regime_status` | CORE | Yes | Current regime health (stable/unstable/collapsed). Set by engine. |
| `protest_risk` | DERIVED | No | `= stability < STABILITY_THRESHOLDS["protest_probable"]`. Derive on demand. |
| `coup_risk` | DERIVED | No | `= stability < STABILITY_THRESHOLDS["regime_collapse_risk"]` for autocracies. Derive on demand. |

### Per-Country: Technology

| Variable | Type | Store? | Justification |
|----------|------|:------:|---------------|
| `nuclear_level` | CORE | Yes | Tech achievement (0-3). Changes on threshold crossing. |
| `nuclear_rd_progress` | CORE | Yes | Accumulated R&D progress toward next level. |
| `nuclear_tested` | DERIVED | No | `= nuclear_level >= 1`. Trivial derivation. |
| `ai_level` | CORE | Yes | Tech achievement (0-4). |
| `ai_rd_progress` | CORE | Yes | Accumulated R&D progress toward next level. |

### Per-Country: Diplomatic

| Variable | Type | Store? | Justification |
|----------|------|:------:|---------------|
| `wars` | DERIVED | No | Filter `ws.wars` for this country. Derive on access. |
| `peace_treaties` | DERIVED | No | Filter `ws.treaties` for this country. Derive on access. |
| `organization_memberships` | DERIVED | No | Filter `ws.org_memberships` for this country. Derive on access. |
| `active_treaties` | DERIVED | No | Filter `ws.treaties` for this country where `status == active`. |

### Global Collections

| Variable | Type | Store? | Justification |
|----------|------|:------:|---------------|
| `countries` | CORE | Yes | Master entity collection. |
| `zones` | CORE | Yes | Map state. Owner and forces change during play. |
| `zone_adjacency` | CONFIG | Yes | Map topology. Set from CSV. Never changes. |
| `deployments` | CORE | Yes | Unit placements. Canonical source for zone forces. |
| `bilateral.tariffs` | CORE | Yes | Tariff levels between country pairs. Changed by player action. |
| `bilateral.sanctions` | CORE | Yes | Sanction levels between country pairs. Changed by player action. |
| `organizations` | CONFIG | Yes | Org definitions. Set from CSV. |
| `org_memberships` | CORE | Yes | Membership can change (join/leave/expel). |
| `wars` | CORE | Yes | Active conflicts. Created/ended by events. |
| `active_theaters` | DERIVED | No | `= unique(war.theater for war in ws.wars)`. Derive from wars list. |
| `chokepoint_status` | CORE | Yes | Blockade state per chokepoint. Changed by military action. |
| `treaties` | CORE | Yes | Agreements created during play. Dynamic. |
| `basing_rights` | CORE | Yes | Military basing agreements. Created during play. |
| `roles` | CORE | Yes | Role state (status, personal_coins). Changes during play. |
| `relationships` | CORE | Yes | Bilateral relationship state. Changes during play. |
| `events_log` | CORE | Yes | Append-only event record. THE behavioral data pipeline. |
| `round_logs` | DERIVED | No | `= group events_log by round`. Derive on access. |
| `ground_blockades` | CORE | Yes | Ground-based blockade state. Set by force positioning. |
| `active_blockades` | CORE | Yes | Chokepoint blockade details. Set by naval action. |
| `rare_earth_restrictions` | CORE | Yes | Per-country restriction level. Set by Cathay action. |

### Per-Role Variables

| Variable | Type | Store? | Justification |
|----------|------|:------:|---------------|
| `personal_coins` | CORE | Yes | Account balance. Changes via allocation and personal investment. |
| `status` | CORE | Yes | active/fired/arrested/incapacitated/dead. Changed by events. |
| `character_name`, `title`, `age`, `gender`, etc. | CONFIG | Yes | Set from CSV. |
| `powers` | CONFIG | Yes | Role capabilities. Set from CSV. |
| `objectives` | CONFIG | Yes | Role goals. Set from CSV. |
| `ticking_clock` | CONFIG | Yes | Personal urgency. Set from CSV. |
| `is_head_of_state` | CORE | Yes | Can change via succession, coup, or election. |
| `is_military_chief` | CORE | Yes | Can change via firing/appointment. |

---

## Classification Summary

| Category | Count | Notes |
|----------|-------|-------|
| CORE (stored) | ~45 | The canonical state. Everything the engine persists. |
| DERIVED (recomputed) | ~18 | Currently stored in world_state.py but SHOULD NOT be. Scheduled for refactor. |
| INTERMEDIATE (transient) | ~8 | Calculation artifacts. Never leave engine memory. |
| CONFIG (static) | ~25 | CSV seed data. Set once. Never modified by engine. |
| DUPLICATE (remove) | ~4 | Flat sector aliases, redundant diplomatic lists. Remove in next refactor. |

---

# PART 3: ENTITY MODEL

```
ENTITIES:

  Country (20)
    +-- id, sim_name, parallel, regime_type, team_type
    +-- has --> Economic State
    |          (gdp, treasury, inflation, debt_burden, sectors, tax_rate,
    |           trade_balance, opec_production, formosa_dependency,
    |           social_spending_baseline)
    +-- has --> Military State
    |          (ground, naval, tactical_air, strategic_missiles, air_defense,
    |           production_costs, production_capacity, maintenance_cost,
    |           mobilization_pool)
    +-- has --> Political State
    |          (stability, political_support, war_tiredness, dem_rep_split,
    |           regime_status)
    +-- has --> Technology State
    |          (nuclear_level, nuclear_rd_progress, ai_level, ai_rd_progress)
    +-- has many --> Roles (2-9 per country)
    +-- belongs to many --> Organizations
    +-- has many --> Deployments (units on zones)
    +-- has many --> Bilateral Relations (with other countries)
    +-- produces --> State Snapshot (per round, immutable once frozen)

  Role (40+)
    +-- id, character_name, parallel, title, age, gender
    +-- belongs to --> Country
    +-- has --> Personal Balance (personal_coins)
    +-- has --> Status (active / fired / arrested / incapacitated / dead)
    +-- has --> Powers (list of capabilities)
    +-- has --> Objectives (list of goals)
    +-- has --> Ticking Clock (personal urgency text)
    +-- has --> Faction (internal political camp)
    +-- has --> Flags (is_head_of_state, is_military_chief, expansion_role, ai_candidate)
    +-- has many --> Artefacts (role pack items)

  Organization (8+)
    +-- id, sim_name, parallel, description
    +-- has --> Decision Rules (decision_rule, voting_threshold)
    +-- has --> Chair (chair_role_id, optional)
    +-- has --> Meeting Schedule (meeting_frequency)
    +-- has many --> Members (countries, with role_in_org and veto status)

  Zone (57+ land + water hexes)
    +-- id, display_name, type, theater, is_chokepoint
    +-- has --> Owner (country_id or "none")
    +-- has --> Forces (per country, per unit type)
    +-- has --> Status (normal / occupied / blockaded / contested)
    +-- has many --> Adjacent Zones (bidirectional, with connection_type)

  War (dynamic, created during play or from initial relationships)
    +-- attacker, defender
    +-- has --> Theater (zone grouping)
    +-- has --> Start Round
    +-- has --> Allies (per side)
    +-- has --> Occupied Zones (list)

  Agreement (dynamic, created during play)
    +-- id (generated)
    +-- has --> Parties (countries and/or roles)
    +-- has --> Terms (structured + free text)
    +-- has --> Type (ceasefire / peace_treaty / trade_deal / alliance / basing_rights)
    +-- has --> Status (proposed / active / breached / expired / dissolved)
    +-- has --> Created (round, timestamp)
    +-- has --> Expiry (round, if applicable)

  Round (8 rounds per SIM)
    +-- round_num
    +-- has --> World State Snapshot (immutable once next round starts)
    +-- has many --> Events (actions, results, transitions)
    +-- has --> Expert Panel Results (Keynes, Clausewitz, Machiavelli assessments)
    +-- has --> Coherence Check Results (flags, auto-fixes)
    +-- has --> Narrative (round briefing text)
    +-- has --> Phase Markers (A start, A end, B start, B end, C start, C end)

  Event (append-only log -- hundreds to thousands per SIM)
    +-- See Part 4 for full schema.
```

### Entity Relationship Summary

```
Country ---< Role              (1:many, 2-9 roles per country)
Country ---< Deployment        (1:many, units across zones)
Country >--< Organization      (many:many, via org_memberships)
Country >--< Country           (many:many, via relationships + bilateral)
Country ---< War               (1:many, as attacker/defender/ally)
Zone    ---< Deployment        (1:many, forces from multiple countries)
Zone    >--< Zone              (many:many, via zone_adjacency)
Role    ---< Artefact          (1:many, role pack items)
Round   ---< Event             (1:many, all events in a round)
Round   --- Snapshot           (1:1, immutable state capture)
Agreement --< Country          (many:many, parties to agreements)
```

### KING Database Mapping

The KING simulation platform uses ~20 tables that partially map to our entities. Key correspondences for future Supabase implementation:

| TTT Entity | KING Table Parallel | Notes |
|------------|-------------------|-------|
| Country | `countries` | Direct mapping. Add economic/military/political/tech sub-objects as JSONB columns or separate tables. |
| Role | `participants` + `roles` | KING splits player identity from role assignment. We should do the same for multi-SIM support. |
| Organization | `organizations` | Direct mapping. |
| Zone | `map_regions` | KING uses simpler region model. We need hex support. |
| Deployment | `unit_placements` | Direct mapping. |
| War | `conflicts` | KING has a conflict table. We should adopt similar structure. |
| Agreement | `agreements` | KING tracks treaties. We need richer type system. |
| Event | `action_log` | KING's action log is our event log. Core behavioral data. |
| Round/Snapshot | `round_states` | KING stores full state per round. We should store deltas + snapshots. |

---

# PART 4: EVENT LOG SCHEMA

The event log is the most important data structure in the system. It is the complete behavioral record of the SIM and the primary input for post-SIM analytics.

## Event Structure

```
EVENT:
  id:           UUID (generated, globally unique)
  round:        int (0-8)
  phase:        'A' | 'B' | 'C' | 'pre' | 'post'
                  A = free action phase (participant decisions + live combat)
                  B = world model processing (between-round batch)
                  C = deployment phase (unit placement)
                  pre = pre-round setup
                  post = post-round wrap-up
  timestamp:    ISO 8601 datetime (e.g., "2026-04-15T14:23:07Z")
  actor:        role_id | 'engine' | 'moderator' | 'system'
                  role_id for participant actions
                  'engine' for automated processing
                  'moderator' for facilitator interventions
                  'system' for infrastructure events
  action_type:  string (from controlled vocabulary -- see below)
  target:       country_id | zone_id | role_id | org_id | null
  details:      JSON (action-specific structured data)
  result:       JSON (outcome data)
  visibility:   'public' | 'country' | 'role' | 'moderator'
  country_context: country_id (which country this event belongs to, for filtering)
```

## Controlled Vocabulary for action_type

### Military Actions
- `attack` -- land, naval, or air attack on a zone
- `deploy_units` -- place units in a zone
- `move_units` -- reposition units between zones
- `blockade_start` -- establish chokepoint blockade
- `blockade_end` -- lift chokepoint blockade
- `nuclear_strike` -- nuclear weapon use
- `nuclear_test` -- nuclear weapons test

### Economic Actions
- `set_tariff` -- change tariff level on a country
- `set_sanctions` -- change sanctions level on a country
- `set_opec_production` -- change OPEC production level
- `set_rare_earth` -- change rare earth restriction level
- `budget_submit` -- submit budget allocations
- `money_print` -- (engine) money printing due to deficit
- `trade_deal` -- bilateral trade agreement

### Diplomatic Actions
- `negotiate` -- open or continue negotiation
- `propose_agreement` -- formal agreement proposal
- `sign_agreement` -- agreement signing
- `breach_agreement` -- violation of existing agreement
- `declare_war` -- war declaration
- `ceasefire` -- ceasefire agreement
- `peace_treaty` -- formal peace
- `join_org` -- join organization
- `leave_org` -- leave organization

### Political Actions
- `election` -- scheduled election event
- `coup_attempt` -- coup triggered by low stability
- `revolution` -- regime change event
- `fire_role` -- head of state fires a team member
- `arrest_role` -- role arrested
- `succession` -- leadership change
- `public_statement` -- public diplomatic statement

### Engine Events
- `gdp_update` -- GDP change (round processing)
- `inflation_update` -- inflation change
- `stability_update` -- stability change
- `state_transition` -- economic state change (normal/stressed/crisis/collapse)
- `contagion` -- cross-country economic contagion
- `expert_panel` -- AI expert panel adjustment
- `coherence_fix` -- auto-correction from coherence check
- `combat_result` -- combat resolution outcome
- `production_complete` -- military production
- `tech_advance` -- technology level increase

### Transaction Actions
- `transfer_coins` -- bilateral coin transfer
- `personal_invest` -- role personal coin investment
- `bribe` -- covert payment
- `aid_package` -- economic aid

## Event Log Rules

1. **Append-only.** Events are never modified or deleted.
2. **Ordered.** Events within a round are ordered by timestamp.
3. **Complete.** Every state change has a corresponding event. If state changed, there is an event explaining why.
4. **Idempotent replay.** Replaying events from initial state produces identical final state (modulo stochastic elements, which store their random seed in event details).
5. **Visibility enforced at query time.** All events are stored with full details. The visibility field controls what is returned by API queries.

---

# PART 5: INFORMATION ASYMMETRY RULES

Detailed specification of what each participant class can see. This is enforced at the API layer (see [F4 API Contracts](SEED_F4_API_CONTRACTS_v1.md)).

## Master Visibility Matrix

| Data Point | Public | Country Team | Role-Specific | Moderator |
|------------|:------:|:------------:|:-------------:|:---------:|
| **Global** | | | | |
| Oil price | Exact | Exact | Exact | Exact |
| Oil price trend (3-round) | Exact | Exact | Exact | Exact |
| OPEC production decisions | Exact | Exact | Exact | Exact |
| Active wars | Exact | Exact | Exact | Exact |
| Chokepoint blockade status | Exact | Exact | Exact | Exact |
| Global trade volume index | Approximate (+/-10%) | Approximate | Approximate | Exact |
| Nuclear use (if any) | Exact | Exact | Exact | Exact |
| **Own Country Economic** | | | | |
| Own GDP | -- | Exact | Exact | Exact |
| Own treasury | -- | Exact | Exact | Exact |
| Own inflation | -- | Exact | Exact | Exact |
| Own debt burden | -- | Exact | Exact | Exact |
| Own economic state | -- | Exact | Exact | Exact |
| Own revenue / budget | -- | Exact | Exact | Exact |
| Own momentum | -- | Exact | Exact | Exact |
| Own market index | -- | Exact | Exact | Exact |
| **Other Country Economic** | | | | |
| Other GDP | Approximate (tier: small/medium/large/major) | -- | Intelligence ops reveal approximate | Exact |
| Other treasury | Hidden | -- | Intelligence ops | Exact |
| Other inflation | Public (reported, may lag 1 round) | -- | Intelligence ops reveal exact | Exact |
| Other economic state | Public (1 round lag for crisis/collapse) | -- | Intelligence | Exact |
| Other debt burden | Hidden | -- | Intelligence | Exact |
| **Military** | | | | |
| Own unit counts (total) | -- | Exact | Exact | Exact |
| Own unit positions | -- | Exact | Exact | Exact |
| Other unit positions (visible zones) | Units in shared/adjacent zones | Units in shared/adjacent zones | Intelligence reveals distant zones | Exact (all) |
| Other total military | Approximate (tier: weak/moderate/strong/superpower) | -- | Intelligence | Exact |
| Combat results | Public (summary) | Exact (own involvement) | Exact (own involvement) | Exact (all) |
| Nuclear capability | Known for declared states | Known for declared + intelligence | Intelligence | Exact |
| **Political** | | | | |
| Own stability | -- | Exact | Exact | Exact |
| Own political support | -- | Exact | Exact | Exact |
| Other stability | Hidden | -- | Intelligence (approximate) | Exact |
| Other political support | Hidden | -- | Intelligence (approximate) | Exact |
| Election results | Public | Public | Public | Public |
| Regime changes | Public | Public | Public | Public |
| **Diplomatic** | | | | |
| Public treaties | Exact | Exact | Exact | Exact |
| Secret agreements | Hidden | Parties only | Parties only | Exact |
| Negotiation in progress | Hidden | Own country only | Intelligence reveals others | Exact |
| Tariff levels | Public | Public | Public | Public |
| Sanction levels | Public | Public | Public | Public |
| **Role-Specific** | | | | |
| Personal coins balance | -- | -- | Own role only | Exact |
| Role artefacts | -- | -- | Own role only | Exact |
| Covert operation results | -- | -- | Ordering role only | Exact |
| Personal investments | -- | -- | Own role only | Exact |
| **Engine Internals** | | | | |
| Expert panel adjustments | -- | -- | -- | Exact |
| Coherence flags / fixes | -- | -- | -- | Exact |
| Formula parameters | -- | -- | -- | Exact |
| Random seeds | -- | -- | -- | Exact |

## Intelligence Operations

Certain roles (typically intelligence chiefs or equivalents) can conduct intelligence operations that reveal normally hidden information. Intelligence results are:
- Delivered as role-specific events (visibility = 'role')
- May be approximate (exact value +/- 10-20% noise) or exact, depending on operation quality
- Delay: results arrive in the same round or next round, depending on operation type
- Can be shared by the receiving role with their team, at their discretion (verbal, in-game)

---

# PART 6: DATA FLOW DIAGRAM

See [F3 Data Flows](SEED_F3_DATA_FLOWS_v1.md) for the complete visual specification. Summary below.

```
ROUND START
  |
  +---> Participants see:
  |       Dashboard (own country state, filtered by COUNTRY/ROLE visibility)
  |       Map (public positions + own forces)
  |       World briefing (public narrative from previous round)
  |
  +---> Phase A: Free Action (REAL-TIME)
  |       |
  |       +-- Participant submits action
  |       +-- Live Action Engine processes immediately
  |       +-- Result --> Event Log (with visibility tag)
  |       +-- Transaction Engine processes bilateral deals
  |       +-- Updated map/state pushed to relevant participants
  |       |
  |       Duration: 30-60 minutes (moderator-controlled)
  |
  +---> Phase B: World Model Processing (BATCH)
  |       |
  |       +-- World Model Engine reads: Full State + Event Log + Actions
  |       +-- Pass 1: Deterministic formulas (14 chained steps)
  |       +-- Pass 2: AI contextual adjustments
  |       +-- Pass 3: Coherence check + narrative generation
  |       +-- Engine writes: Updated State Snapshot + Events + Narrative
  |       |
  |       +-- Participants see:
  |       |     Country briefing (own data only, COUNTRY visibility)
  |       |     World narrative (PUBLIC)
  |       +-- Moderator sees:
  |             Everything + expert panel flags + coherence results
  |       |
  |       Duration: < 5 minutes (target)
  |
  +---> Phase C: Deployment (REAL-TIME, structured)
  |       |
  |       +-- Participants deploy/reposition units
  |       +-- Deployment updates --> Event Log
  |       +-- Map updated with new positions
  |       |
  |       Duration: 10-15 minutes
  |
  +---> ROUND END
          |
          +-- State Snapshot frozen (IMMUTABLE)
          +-- Round advances
```

---

# PART 7: API CONTRACTS

See [F4 API Contracts](SEED_F4_API_CONTRACTS_v1.md) for the complete specification. Summary of interfaces below.

## Interface 1: Participant <--> Backend

```
READ:
  GET  /state/{round}/{country_id}     Own country state (visibility-filtered)
  GET  /map/{round}                    Public map state + own forces
  GET  /events/{round}                 Events visible to requesting role
  GET  /briefing/{round}               Round narrative (public + own country)
  GET  /role/{role_id}                 Own role data (personal coins, artefacts)

WRITE:
  POST /actions/{round}/{country_id}   Submit country actions for the round
  POST /deploy/{round}/{country_id}    Submit deployment orders
  POST /transactions                   Propose bilateral deal (requires counterparty confirm)
  POST /statements                     Issue public statement
```

## Interface 2: Backend <--> World Model Engine

```
INPUT:
  {
    round_num: int,
    world_state: WorldState (full, unfiltered),
    country_actions: { country_id: { budget, tariffs, sanctions, military, diplomatic } },
    event_log: [ Event, ... ]
  }

OUTPUT:
  {
    round_num: int,
    new_world_state: WorldState,
    events: [ Event, ... ],
    narrative: string,
    expert_panel: { keynes: [], clausewitz: [], machiavelli: [], applied: [], flags: [] },
    coherence_flags: [ { severity, description, auto_fixed } ]
  }
```

## Interface 3: Backend <--> Live Action Engine

```
INPUT:
  {
    action_type: string,
    actor: role_id,
    params: { (action-specific) },
    current_state: WorldState (full)
  }

OUTPUT:
  {
    success: bool,
    result: { (action-specific outcome) },
    state_changes: [ { path, old_value, new_value } ],
    events: [ Event, ... ],
    error: string | null
  }
```

## Interface 4: Backend <--> Transaction Engine

```
INPUT:
  {
    transaction_type: string (transfer_coins, trade_deal, basing_rights, aid_package),
    proposer: role_id,
    counterparty: role_id,
    details: { (type-specific) },
    current_state: WorldState
  }

OUTPUT:
  {
    success: bool,
    state_changes: [ { path, old_value, new_value } ],
    events: [ Event, ... ],
    requires_confirmation: bool,
    confirmation_token: string | null,
    error: string | null
  }
```

## Interface 5: Backend <--> AI Participant

```
INPUT:
  {
    role_id: string,
    role_brief: string (prose brief),
    visible_state: WorldState (filtered by role visibility),
    available_actions: [ { action_type, constraints, costs } ],
    round_context: { round_num, phase, time_remaining, recent_events },
    objectives: [ string ],
    ticking_clock: string
  }

OUTPUT:
  {
    actions: [ { action_type, params, priority, reasoning } ],
    negotiations: [ { target_role, proposal, reasoning } ],
    statements: [ { audience, content } ],
    internal_reasoning: string (moderator-visible only)
  }
```

---

# PART 8: DATA MAINTENANCE DISCIPLINE

These rules prevent the ad-hoc growth that created the current mess in `world_state.py`.

## Rules for Adding New Variables

### 1. The Derivation Test

BEFORE adding any variable to the world state, answer this question:

> **Can this value be DERIVED from existing CORE variables + event history?**

- If YES: add a derivation function. NOT a stored variable.
- If NO: add to CORE with full justification documented below.

### 2. CORE Variable Requirements

Every new CORE variable must have ALL of the following documented:

| Requirement | Description |
|-------------|-------------|
| **Name** | Lowercase, snake_case, descriptive |
| **Type** | Python type (int, float, str, bool, list, dict) |
| **Valid range** | Min/max values, or enumerated options |
| **Starting value** | Default or CSV-loaded |
| **Which engine step updates it** | Step number and function name |
| **Which consumers read it** | List of engine steps, UI components, AI agents |
| **Visibility level** | public / country / role / moderator |
| **Justification** | Why this cannot be derived |

### 3. DERIVED Variable Requirements

Every derived variable must have:

| Requirement | Description |
|-------------|-------------|
| **Derivation formula** | Referencing CORE variables by name |
| **Where computed** | Engine step or on-demand accessor |
| **Caching rules** | Compute once per round? On every access? Memoized? |
| **Consumers** | Who needs this derived value |

### 4. The Convenience Rule

**NEVER add a variable "just for convenience."**

If a heuristic check needs a counter (e.g., "rounds under sanctions"), derive it from the event log. If a display needs a formatted value, compute it in the display layer. If an optimization needs a cache, put it in a clearly-labeled cache dict with a `_cache` suffix, not in the state model.

### 5. Periodic Audit

Every major iteration (approximately quarterly during development), audit ALL variables:

- Is this variable still used by any consumer?
- Can this variable now be derived (due to new event types or formula changes)?
- Is there duplication between this variable and another?
- Does the valid range still match engine behavior?

## Change Management for Data Schema

### Adding a CORE Variable

1. Document in the variable classification table (Part 2 of this document)
2. Add to the data dictionary with all required fields
3. Update CSV schema in [F1 Data Schema](SEED_F1_DATA_SCHEMA_v1.md) if loaded from CSV
4. Update `WorldState.__init__()` with default value
5. Update `WorldState.to_dict()` and `WorldState.from_dict()` for serialization
6. Update information asymmetry rules (Part 5 of this document)
7. Update API visibility filtering in [F4 API Contracts](SEED_F4_API_CONTRACTS_v1.md)
8. Add validation rule if applicable
9. **Marat approval required** if the variable expands simulation scope

### Removing a Variable

1. Verify no consumer depends on it (search all engine files, test files, UI components)
2. Archive -- do NOT delete. Mark as `deprecated` in schema with date and reason
3. Update engine code to use derivation instead (if replacing stored with derived)
4. Keep in `from_dict()` for backward compatibility with existing snapshots
5. Remove from `to_dict()` to stop persisting
6. Update documentation

### Modifying a Variable

1. Document the change with before/after in this document
2. Verify all consumers handle the new type/range
3. Add migration logic for existing snapshots if type changes
4. Update validation rules

## Anti-Patterns to Avoid

| Anti-Pattern | Why It Is Bad | What to Do Instead |
|-------------|--------------|-------------------|
| Storing derived counters (e.g., `crisis_rounds`) | State drift if replay disagrees with counter | Derive from snapshot history |
| Duplicate fields (e.g., `sector_resources` AND `sectors.resources`) | Divergence risk, confusing API | Single source, accessor function |
| Intermediate values in state (e.g., `oil_revenue`) | Meaningless between rounds, wastes storage | Keep in engine local variables |
| Flag fields for event-based checks (e.g., `formosa_resolved`) | Redundant with event log | Query event log |
| Unbounded string fields for structured data | Hard to query, validate, or migrate | Use typed fields or controlled vocabulary |

---

# APPENDIX A: DATA DICTIONARY (CORE VARIABLES)

Quick reference for all stored CORE variables with their specifications.

## Global

| Name | Type | Range | Default | Updated By | Visibility |
|------|------|-------|---------|-----------|-----------|
| round_num | int | 0-8 | 0 | Orchestrator | public |
| oil_price | float | 30-250 | 80.0 | WM Step 1 | public |
| global_trade_volume_index | float | 0-200 | 100.0 | WM Step 11 | moderator (approx public) |
| nuclear_used_this_sim | bool | T/F | false | LA Engine | public (if true) |
| formosa_blockade | bool | T/F | false | LA Engine | public |
| dollar_credibility | float | 20-100 | 100.0 | WM Step 13 | moderator |

## Per-Country Economic

| Name | Type | Range | Default | Updated By | Visibility |
|------|------|-------|---------|-----------|-----------|
| gdp | float | 0.5+ | CSV | WM Step 2 | country |
| treasury | float | 0+ | CSV | WM Step 4 | country |
| inflation | float | 0-500 | CSV | WM Step 7 | country |
| debt_burden | float | 0+ | CSV | WM Step 8 | country |
| momentum | float | -5 to +5 | 0.0 | WM Step 10 | country |
| opec_production | enum | low/normal/high/na | CSV | Player action | public |

## Per-Country Military

| Name | Type | Range | Default | Updated By | Visibility |
|------|------|-------|---------|-----------|-----------|
| ground | int | 0+ | CSV | WM Step 5 / LA | country |
| naval | int | 0+ | CSV | WM Step 5 / LA | country |
| tactical_air | int | 0+ | CSV | WM Step 5 / LA | country |
| strategic_missiles | int | 0+ | CSV | WM Step 5 | country |
| air_defense | int | 0+ | CSV | LA Engine | country |

## Per-Country Political

| Name | Type | Range | Default | Updated By | Visibility |
|------|------|-------|---------|-----------|-----------|
| stability | float | 1-10 | CSV | WM Step 12 | country |
| political_support | float | 0-100 | CSV | WM Step 13 | country |
| war_tiredness | float | 0+ | CSV | WM Step 12 | country |
| regime_status | enum | stable/unstable/collapsed | "stable" | WM post-step | country |

## Per-Country Technology

| Name | Type | Range | Default | Updated By | Visibility |
|------|------|-------|---------|-----------|-----------|
| nuclear_level | int | 0-3 | CSV | WM Step 6 | country (public if declared) |
| nuclear_rd_progress | float | 0-1 | CSV | WM Step 6 | country |
| ai_level | int | 0-4 | CSV | WM Step 6 | country |
| ai_rd_progress | float | 0-1 | CSV | WM Step 6 | country |

## Per-Role

| Name | Type | Range | Default | Updated By | Visibility |
|------|------|-------|---------|-----------|-----------|
| personal_coins | float | 0+ | CSV | Transaction Engine | role |
| status | enum | active/fired/arrested/incapacitated/dead | "active" | LA / Moderator | country |
| is_head_of_state | bool | T/F | CSV | Event (succession) | public |
| is_military_chief | bool | T/F | CSV | Event (appointment) | country |

---

# APPENDIX B: MIGRATION PATH

## Current State (SEED Phase)

- Data lives in CSVs (seed) and JSON snapshots (engine output)
- `world_state.py` stores CORE + DERIVED + INTERMEDIATE indiscriminately
- No visibility enforcement -- all data accessible to all consumers
- Event log exists but is not the primary state record

## Target State (BUILD Phase)

- Data lives in Supabase (PostgreSQL)
- CORE variables stored in database tables matching entity model
- DERIVED variables computed by engine and API layer, never stored
- Visibility enforced at API query layer (row-level security)
- Event log is append-only table, primary behavioral record
- State snapshots stored as JSONB per round for fast access

## Migration Steps

1. **Refactor world_state.py** -- remove all DERIVED and INTERMEDIATE variables from `__init__`, `to_dict`, `from_dict`. Add derivation functions.
2. **Remove duplicates** -- eliminate flat sector aliases, redundant diplomatic sub-dicts.
3. **Add visibility metadata** -- tag each field with its visibility level.
4. **Schema Supabase tables** -- map entity model to PostgreSQL tables. Each CSV becomes one table.
5. **Implement API layer** -- visibility filtering based on authenticated role.
6. **Event log as table** -- append-only, indexed by round + actor + action_type.

---

*This document is the single reference for TTT data architecture decisions. All engine, API, and UI development must conform to the classifications and rules specified here. Changes require updating this document first.*
