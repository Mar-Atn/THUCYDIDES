# F1 — Template / Scenario / Sim-Run Taxonomy

**Version:** 1.0 | **Date:** 2026-04-12 | **Status:** Locked, ready for upward reconciliation
**Drives the design update of:** `3 DETAILED DESIGN/DET_F_SCENARIO_CONFIG_SCHEMA.md`, `2 SEED/C_MECHANICS/SEED_C_MAP_UNITS_MASTER_v1.md`, `1. CONCEPT/` (where applicable)

> This document captures the canonical 3-level data model that emerged from
> the F1 vertical slice. After all action slices are complete, it will be
> the source for the systemic design document update upwards (DET → SEED →
> CONCEPT). Until then, the application code uses these definitions and
> the rest of the design docs are out-of-date.

---

## Why this model exists

Before F1 (2026-04-11), every per-round snapshot row in the DB was keyed by
`(scenario_id, round_num)`. There was no way to run the same scenario
twice without trampling the previous run's data. Tests worked around this
by hacking magic round numbers like `200, 201` to avoid colliding with the
canonical R0-R8 range. Calibration runs were impossible because they
needed dozens of independent playthroughs.

F1 introduced **sim_run** as the unit of isolation: every per-round write
now belongs to a specific run. Runs are immutable artifacts. Scenarios are
reusable fixtures. Templates are versioned game definitions. This matches
the model already documented in `DET_F_SCENARIO_CONFIG_SCHEMA.md` but never
implemented in the hot-path tables.

---

## The 3 levels — canonical definition

```
TEMPLATE v1.0 "Power Transition 2026"          ← versioned, slow-evolving
   │
   ├── SCENARIO "start_one"                    ← reusable test fixture
   ├── SCENARIO "test_m1_movement"             ← (future) minimal movement setup
   ├── SCENARIO "test_m2_ground_combat"        ← (future) pre-positioned forces
   ├── SCENARIO "demo_full_game"               ← (future) the real 6-8 round showcase
   │
   └── for each scenario:
       ├── SIM-RUN  2026-04-11 14:32  seed=42  AI=Gemini
       ├── SIM-RUN  2026-04-11 15:10  seed=99  AI=Gemini   ← same scenario, different seed
       ├── SIM-RUN  2026-04-12 09:00  seed=42  AI=Anthropic ← same scenario, different LLM
       └── SIM-RUN  2026-04-12 14:15  seed=42  paused at R3
```

### TEMPLATE — the game itself
- Versioned (semver + name): `v1.0 "Power Transition 2026"`, `v1.1 …`, `v2.0 …`
- **Owns:**
  - Map topology (hexes, adjacency, theaters, chokepoints)
  - Country master list with starting structural data (GDP, sectors, military potentials, tech levels)
  - Role library + default character sheets / personas / briefings
  - Action catalog (referenced — code-backed)
  - Formula coefficients (LOCKED per version — preserves calibration)
  - Default relationship matrix
  - Default unit deployment layout
  - Allowed round-count range
  - Allowed oil-price range
  - Allowed theater set
- **Frozen per version.** Changes go in a new version, never edits an existing one.

### SCENARIO — one event's configuration
- Identity: `(template_id FK, code, name, event_metadata, created_at)`
- **Owns (no template default exists for these):**
  - Event metadata (venue, facilitator, participant profile, learning objectives, delivery format)
  - SIM starting date (in-fiction)
  - Max rounds chosen (must be in template's allowed range)
  - Oil price starting value
  - Theater activation (which template theaters are ON)
  - Role assignments (which template roles are active + bindings)
  - Election schedule
  - Scripted event timeline
- **Sparse overrides (optional, fall back to template if unset):**
  - `country_stat_overrides` JSONB
  - `relationship_overrides` JSONB
  - `role_briefing_overrides` JSONB
  - `role_persona_overrides` JSONB
  - `unit_layout_id` FK (or NULL = template default)
- **Reusable.** A scenario is defined once, used by hundreds of runs. No
  per-round state lives here.

### SIM-RUN — one playthrough
- Identity: `(scenario_id FK, name, description, status, current_round, max_rounds, seed, created_at, finalized_at)`
- **Owns:** every per-round state row (snapshots, decisions, events, combat
  results, memories, transactions). All keyed by `sim_run_id` from F1
  onwards.
- **Lifecycle:**
  ```
  setup        ← create_run() drops here
    ↓
  active       ← orchestrator starts ticking rounds
    ↓
  paused       ← (optional)
    ↓
  completed | aborted | visible_for_review | archived
  ```
- **Immutable once finalized.** A run is a historical artifact.
- **Cascade-deletable.** `DELETE FROM sim_runs WHERE id = ?` cleans every
  child row in one shot (foreign keys do the work).

### CODE — hard-coded
- Engine implementations (parameters flow from template)
- Action catalog
- Event type taxonomy
- 4-block cognitive architecture
- Round phase structure (Phase A / Phase B)
- UI layouts, Realtime, Auth, API
- **Versioned via code releases.** Changes here are commits, not data.

---

## Boundaries — who owns what

| Concern | Template | Scenario | Sim-Run | Code |
|---|---|---|---|---|
| Map topology | ✅ frozen | (read) | (read) | imports |
| Country structural stats | ✅ default | sparse override | snapshot at R0+ | (none) |
| Formula coefficients | ✅ LOCKED | (read) | (read) | implements |
| Starting unit layout | ✅ default | override | snapshot at R0 | (none) |
| Role library | ✅ default | active list + bindings | role_state per round | (none) |
| Per-round country state | (none) | (none) | ✅ owns | (none) |
| Per-round unit positions | (none) | (none) | ✅ owns | (none) |
| Combat results | (none) | (none) | ✅ owns | resolves |
| Decisions / actions | (none) | (none) | ✅ owns | validates |
| Agent memories | (none) | (none) | ✅ owns | (none) |
| Engine logic | (none) | (none) | (none) | ✅ owns |
| Action catalog | (referenced) | (referenced) | (none) | ✅ owns |
| Round phases | (none) | (none) | (none) | ✅ owns |

---

## DB schema state (post-F1, 2026-04-12)

### `sim_runs` table — lifecycle fields added in F1
```
id              uuid PK (default uuid_generate_v4)
scenario_id     uuid FK → sim_scenarios(id)
name            text NOT NULL
description     text                       ← F1
seed            bigint                     ← F1
status          text NOT NULL              ← F1: enum extended
                  ('setup'|'active'|'paused'|'completed'|'aborted'
                   |'archived'|'visible_for_review')
current_round   integer NOT NULL DEFAULT 0
max_rounds      integer NOT NULL DEFAULT 8
current_phase   text NOT NULL DEFAULT 'pre' (enum)
run_config      jsonb NOT NULL DEFAULT '{}'
created_at      timestamptz NOT NULL DEFAULT now()
started_at      timestamptz
completed_at    timestamptz
finalized_at    timestamptz                ← F1
updated_at      timestamptz NOT NULL DEFAULT now()
```

### 12 hot-path tables — re-keyed to `sim_run_id` in F1
| Table | Old key | New key | Notes |
|---|---|---|---|
| `country_states_per_round` | `(scenario_id, round_num, country_code)` | `(sim_run_id, round_num, country_code)` | Composite UNIQUE swapped. |
| `unit_states_per_round` | `(scenario_id, round_num, unit_code)` | `(sim_run_id, round_num, unit_code)` | Composite UNIQUE swapped. |
| `global_state_per_round` | `(scenario_id, round_num)` | `(sim_run_id, round_num)` | Composite UNIQUE swapped. |
| `round_states` | `(scenario_id, round_num)` | `(sim_run_id, round_num)` | Composite UNIQUE swapped. |
| `agent_memories` | `(scenario_id, country_code, memory_key)` | `(sim_run_id, country_code, memory_key)` | Composite UNIQUE swapped. |
| `agent_decisions` | (no composite) | sim_run_id NOT NULL added | ORDER BY created_at on read. |
| `covert_ops_log` | (no composite) | sim_run_id NOT NULL added | |
| `exchange_transactions` | (no composite) | sim_run_id NOT NULL added | |
| `agreements` | (no composite) | sim_run_id NOT NULL added | |
| `observatory_events` | (no composite) | sim_run_id NOT NULL added | |
| `observatory_combat_results` | (no composite) | sim_run_id NOT NULL added | |
| `pre_seeded_meetings` | (no composite) | sim_run_id NOT NULL added | |

`scenario_id` is **kept on every table as a denorm field** to avoid
re-doing JOINs in the Observatory and engine read paths. It will be
dropped in a later cleanup once nothing reads from it directly.

### Indexes added
```
country_states_per_round (sim_run_id, round_num)
unit_states_per_round    (sim_run_id, round_num)
global_state_per_round   (sim_run_id, round_num)
round_states             (sim_run_id, round_num)
agent_decisions          (sim_run_id, round_num)
observatory_events       (sim_run_id, round_num)
```

### Backfill — the legacy archived run
The pre-F1 default run id `00000000-0000-0000-0000-000000000001` was
re-purposed as the **legacy archived run** for the `start_one` scenario.
Every pre-F1 row (100 country states, 11,040 unit states, 213 events, …)
was backfilled into this run. It carries `status='archived'` and
`description='Legacy pre-F1 data: …'`.

It is browseable from the Observatory selector for historical reference.

### Temporary DB default — to be dropped
The 12 hot tables have `sim_run_id DEFAULT '00000000-0000-0000-0000-000000000001'`
applied via `sim_run_id_temporary_default` migration. This unblocks pre-F1
test fixtures that insert rows directly without knowing about sim_run_id.
It will be dropped in **F1.1 polish** after all slice tests are migrated to
`create_isolated_run()`.

---

## Engine API surface (post-F1)

The engine accepts either a `sim_run_id` (UUID) or a `scenario_code` like
`'start_one'` at every public entry point. A scenario code resolves to the
**legacy archived run** for that scenario via `resolve_sim_run_id()`. A
fresh run id resolves directly. This dual-input compatibility lets pre-F1
code continue to work unchanged while new code passes explicit run ids.

### Public functions
```python
# engine/services/sim_run_manager.py
create_run(scenario_code, name, description?, seed?, max_rounds=8) -> sim_run_id
seed_round_zero(sim_run_id, source_run_id?) -> {country_states, unit_states, global_state}
finalize_run(sim_run_id, status='completed', notes?) -> None
get_run(sim_run_id) -> dict
list_runs(scenario_code?, status?, limit=50) -> list[dict]
resolve_sim_run_id(scenario_code_or_uuid) -> sim_run_id   # the dual-input resolver
get_scenario_id_for_run(sim_run_id) -> scenario_id

# engine/round_engine/resolve_round.py
resolve_round(run_or_scenario, round_num) -> dict          # accepts uuid or code

# engine/engines/round_tick.py
run_engine_tick(run_or_scenario, round_num) -> dict        # accepts uuid or code

# engine/services/*_context.py — each takes optional sim_run_id kwarg
build_budget_context(country_code, scenario_code, round_num, sim_run_id=None) -> dict
build_tariff_context(country_code, scenario_code, round_num, sim_run_id=None) -> dict
build_sanction_context(country_code, scenario_code, round_num, sim_run_id=None) -> dict
build_opec_context(country_code, scenario_code, round_num, sim_run_id=None) -> dict
build_movement_context(country_code, scenario_code, round_num, sim_run_id=None) -> dict
```

### Test helpers
```python
# tests/_sim_run_helper.py
legacy_run_id(scenario_code='start_one') -> sim_run_id
create_isolated_run(scenario_code='start_one', test_name='unnamed', seed_r0=True)
    -> (sim_run_id, cleanup_callable)
```

---

## Observatory contract (post-F1)

`/api/observatory/sim_runs` returns runs with `status IN ('visible_for_review', 'archived')`,
each enriched with the `scenario_code` of its scenario. The selector shows:

```
F1 demo run · R0–0 · start_one · visible_for_review
Thucydides Trap — Default Session · R0–8 · start_one · archived
```

All data endpoints (`units`, `countries`, `events`, `combats`, `blockades`,
`global-series`) accept an optional `sim_run_id` query parameter and
filter by it. When omitted, they fall back to the legacy archived run for
the requested `scenario` (preserving pre-F1 behavior).

JS state object now carries `simRunId`. The selector pins it; "live" mode
clears it.

---

## What changed vs. the pre-F1 design docs

The current `DET_F_SCENARIO_CONFIG_SCHEMA.md` correctly described the
3-level model but never reached the hot tables. F1 implementation matches
the spec. The discrepancies to reconcile in the upward pass are:

1. **`sim_runs` lifecycle fields** — DET docs mention `status` enum; we
   added `description`, `seed`, `finalized_at`. Spec needs updating.
2. **Status enum values** — DET says `setup|active|paused|completed|aborted`;
   F1 added `archived` and `visible_for_review`. Spec needs updating.
3. **Per-round table foreign keys** — DET schema for the 12 hot tables
   showed `scenario_id` only; F1 added `sim_run_id NOT NULL`. Spec needs
   updating.
4. **Composite uniqueness** — DET schema showed `(scenario_id, round_num, …)`;
   F1 swapped to `(sim_run_id, round_num, …)`. Spec needs updating.
5. **Cascade behavior** — DET silent on this; F1 added `ON DELETE CASCADE`
   from `sim_run_id` so deleting a run cleans children. Spec needs updating.
6. **Run lifecycle helpers** — DET silent on `create_run`/`finalize_run`/
   `seed_round_zero`; F1 introduced `sim_run_manager` as the canonical
   service. Spec needs section.
7. **Observatory selector** — DET mentions a "test run browser" loosely;
   F1 wires `sim_runs` directly with `visible_for_review` filter. Spec
   needs section.

---

## Open items deferred to F1.1 (later cleanup sprint)

1. Migrate every slice test to `create_isolated_run()` for true per-test
   isolation (instead of sharing the legacy run via the DB default).
2. Drop the temporary `sim_run_id` DB defaults applied in
   `sim_run_id_temporary_default` migration.
3. Drop the redundant `scenario_id` denorm column from the 12 hot tables
   once nothing reads from it directly.
4. Build a scenario authoring API (`create_scenario(template_code, …)`)
   parallel to `create_run`. Right now scenarios are inserted manually.
5. Decide whether `current_round <= 8` CHECK on `sim_runs` should be
   widened (test runs may want longer or shorter ranges).
6. Cross-LLM run comparison UI (compare two runs of the same scenario
   side-by-side in the Observatory).

---

## Rationale notes for upward reconciliation

These are the design choices baked into F1 that should NOT be reopened
during the DET/SEED/CONCEPT update unless there's a strong reason:

1. **Runs are immutable.** Once finalized, snapshots don't change. The
   current_round counter advances during `setup` → `active` → `completed`
   only. No "edit a past round" affordance.
2. **One template per run, no inheritance chains.** A run binds one
   scenario which binds one template version. No template promotion mid-run.
3. **Sparse scenario overrides, not full copies.** Scenarios store only
   what they want to change vs the template. The runtime merger reconciles.
4. **`scenario_id` denorm is temporary.** It was kept to avoid breaking
   too many JOINs in one go. Drop in F1.1.
5. **Dual-input entry points are temporary.** `resolve_round(scenario_code_or_uuid)`
   accepts both during the F1 transition. F1.1 forces sim_run_id only.
6. **Cascade delete from `sim_runs` is the canonical cleanup path.** No
   manual `DELETE FROM country_states_per_round WHERE sim_run_id = ?`
   anywhere — always delete the run row and let cascades handle children.
7. **Tests own their runs.** A test that wants isolation creates a run,
   exercises it, and either cascade-deletes or finalizes for review. The
   test owns the run's whole lifecycle.
8. **The Observatory is a viewer, not a writer.** It never creates or
   modifies runs — it lists, filters, and displays. Run lifecycle is
   driven by the engine and tests.

---

## Files added or substantially changed by F1

### New
- `app/engine/services/sim_run_manager.py` (309 lines) — lifecycle service
- `app/tests/_sim_run_helper.py` (66 lines) — test helpers
- `app/tests/layer2/test_sim_run_manager.py` (151 lines) — 9 tests
- `PHASES/UNMANNED_SPACECRAFT/PLAN_F1_SIM_RUNS.md` — execution plan
- `PHASES/UNMANNED_SPACECRAFT/F1_TAXONOMY.md` — this document

### Migrated to sim_run_id internally
- `app/engine/round_engine/resolve_round.py` (1811 lines)
- `app/engine/engines/round_tick.py` (652 lines)
- `app/engine/services/budget_context.py`
- `app/engine/services/tariff_context.py`
- `app/engine/services/sanction_context.py`
- `app/engine/services/opec_context.py`
- `app/engine/services/movement_context.py`
- `app/engine/agents/full_round_runner.py`
- `app/engine/agents/leader_round.py`
- `app/engine/agents/tools.py`
- `app/test-interface/server.py` (Observatory API)
- `app/test-interface/static/observatory.js` (selector + state)
- `app/test-interface/templates/observatory.html` (selector dropdown)

### Deleted
- `app/engine/services/test_run_registry.py` — superseded by sim_run lifecycle
- `test_runs` DB table — superseded by `sim_runs` filter

### Migrations applied
- `sim_run_foundation_v1` — schema migration with backfill
- `sim_run_id_temporary_default` — DB default trick (to be dropped in F1.1)

---

## Status banner for the Phase board

> **F1 — Sim Run Foundation** ✅ DONE 2026-04-12.
> 12 hot-path tables re-keyed by `sim_run_id`. Lifecycle service shipped.
> Engine entry points dual-input compatible. Observatory rebuilt around
> `sim_runs` selector. 458 L1 + 19 L2 persistence + 7 L2 sanction-context
> + L3 budget-AI full chain all green. Open items deferred to F1.1.
