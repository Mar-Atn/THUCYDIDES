# Foundation: Data Foundation (M3)

## Template → Scenario → Sim-Run Hierarchy

```
TEMPLATE (master game design, semver-tracked)
  └── SCENARIO (sparse override for one event)
        └── SIM-RUN (one playthrough, immutable once started)
```

**Spec:** `3 DETAILED DESIGN/F1_TAXONOMY.md`, `DET_F_SCENARIO_CONFIG_SCHEMA.md`

## Key DB Tables

### Core hierarchy
- `sim_templates` — game definitions (Template v1.0 "Power Transition 2026")
- `sim_scenarios` — event configurations (FK to template)
- `sim_runs` — individual playthroughs (FK to scenario, status lifecycle)

### Per-round state (keyed by sim_run_id + round_num)
- `country_states_per_round` — all country metrics (GDP, stability, support, tech, etc.)
- `unit_states_per_round` — unit positions and status
- `global_state_per_round` — oil price, market indexes, wars, blockades

### Game entities (keyed by sim_run_id)
- `run_roles` — per-run mutable role state (status, HoS flag, personal coins)
- `power_assignments` — military/economic/foreign_affairs delegation
- `basing_rights` — host↔guest military permissions
- `exchange_transactions` — asset transfer proposals and execution
- `agreements` — diplomatic commitments with signatory tracking

### Elections
- `election_nominations` — candidate registration
- `election_votes` — secret ballots
- `election_results` — outcome with full vote breakdown

### Observatory
- `observatory_events` — all action outcomes, logged with payload
- `observatory_combat_results` — combat details (rolls, modifiers)

### Agent
- `agent_decisions` — submitted actions (with processed_at tracking)
- `agent_memories` — persistent per-role memory across rounds

**Full schema:** `3 DETAILED DESIGN/DET_B1_DATABASE_SCHEMA.sql` v1.3 + `DET_B1_SCHEMA_ADDENDUM_BUILD.sql`

## Seed Data (Template v1.0)
- 21 countries (`2 SEED/C_MECHANICS/C4_DATA/countries.csv`)
- 41 roles (`roles.csv`)
- 346 units (`units.csv`)
- 183 zones (`zones.csv`)
- 247 adjacencies (`zone_adjacency.csv`)
- 381 relationships (`relationships.csv`)
- 10 organizations + 61 memberships
- 30 tariff pairs, 37 sanction pairs
- 2 theater maps (Eastern Ereb, Mashriq)
- 1 global map (10×20 hex grid)

## Key Services
- `sim_run_manager.py` — create_run, seed_round_zero, finalize_run, resolve_sim_run_id
- `run_roles.py` — seed_run_roles, get/update role status
- `power_assignments.py` — seed defaults, check authorization, reassign
