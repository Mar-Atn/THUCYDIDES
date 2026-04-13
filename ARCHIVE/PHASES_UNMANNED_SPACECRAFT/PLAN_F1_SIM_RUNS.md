# PLAN F1 — Sim Run Foundation

**Status:** DRAFT for review | **Owner:** Marat + Build Team | **Drafted:** 2026-04-11
**Scope:** Foundational cleanup before M2 Ground Combat
**Precedes:** M2 (combat), M3 (air), M4 (naval), M5 (blockades), M6 (nuclear)

---

## Why F1 exists

Today the DB schema is in a **split state**:

- 30 tables are already keyed by `sim_run_id` (good — matches CONCEPT/SEED design)
- **12 hot-path tables are keyed by `scenario_id, round_num`** — and these are exactly the ones every slice writes to

**The 12 hot tables (need migration):**

| Table | Used by |
|---|---|
| `country_states_per_round` | All 4 economic slices + movement |
| `unit_states_per_round` | Movement, military |
| `global_state_per_round` | Oil price, OPEC, orchestrator |
| `round_states` | Every resolve_round call |
| `agent_decisions` | All 4 slice audit trails |
| `agent_memories` | Cognitive persistence |
| `covert_ops_log` | Sprint B covert ops |
| `exchange_transactions` | Transaction engine |
| `agreements` | Agreement engine |
| `observatory_events` | Observatory Activity feed |
| `observatory_combat_results` | Observatory Maps |
| `pre_seeded_meetings` | Scenario scripted events |

**Consequence of the split:** any two tests using the same `scenario_code` trample each other's snapshots. That's why `test_movement_full_chain_ai.py` has to hack round 200-201 offsets to avoid colliding with real test data at R0-R10. Every new slice inherits this hack.

**Canonical model (from `DET_F_SCENARIO_CONFIG_SCHEMA.md` and CONCEPT):**

```
TEMPLATE v1.0  →  SCENARIO (e.g. "test_m1_movement")  →  SIM-RUN (one playthrough, R0..RN)
                                                      →  SIM-RUN (another playthrough, different seed)
```

Every `*_per_round` write belongs to a specific **sim_run**, not a scenario. Rounds always start at 0 or 1. Runs are immutable artifacts. Scenarios are reusable test fixtures.

---

## Outcome — definition of done

1. All 12 hot-path tables keyed by `(sim_run_id, round_num)` with `sim_run_id` FK to `sim_runs`.
2. `sim_runs` table has `status` enum (`active`, `completed`, `archived`, `visible_for_review`), `name`, `description`, `seed`, `created_at`.
3. All engine services, validators, context builders, and `resolve_round` take `sim_run_id` (not `scenario_code`) as their primary input.
4. A `sim_run_manager` service provides `create_run(scenario_code, name, ...)`, `finalize_run(sim_run_id, status)`, `list_runs(filter)`.
5. `test_runs` metadata table **deleted** — Observatory reads `sim_runs` directly.
6. Observatory "Test Run" selector lists `sim_runs` rows (name + scenario + timestamp + round_count), jumps to R0 of the selected run.
7. **All existing slice tests rewritten** to create their own sim_run at the start, run rounds 0-1 normally, finalize at end with `status='visible_for_review'`.
8. **Zero** round-200-hack survivors in any test file.
9. All 4 economic + 1 movement vertical-slice tests (L1/L2/L3) green against the new model.

---

## Step-by-step execution

### Step 1 — Schema migration `sim_run_foundation_v1`

SQL draft:

```sql
-- 1a. Extend sim_runs with lifecycle fields
ALTER TABLE sim_runs
  ADD COLUMN IF NOT EXISTS name text,
  ADD COLUMN IF NOT EXISTS description text,
  ADD COLUMN IF NOT EXISTS seed bigint,
  ADD COLUMN IF NOT EXISTS status text NOT NULL DEFAULT 'active'
    CHECK (status IN ('active','completed','archived','visible_for_review')),
  ADD COLUMN IF NOT EXISTS finalized_at timestamptz;

-- 1b. Add sim_run_id to the 12 hot-path tables + backfill legacy run
INSERT INTO sim_runs (scenario_id, name, status, created_at)
  SELECT id, 'legacy_start_one', 'archived', now()
  FROM sim_scenarios WHERE code = 'start_one'
  ON CONFLICT DO NOTHING
  RETURNING id;  -- captured as @legacy_run_id

ALTER TABLE country_states_per_round  ADD COLUMN IF NOT EXISTS sim_run_id uuid REFERENCES sim_runs(id);
ALTER TABLE unit_states_per_round     ADD COLUMN IF NOT EXISTS sim_run_id uuid REFERENCES sim_runs(id);
ALTER TABLE global_state_per_round    ADD COLUMN IF NOT EXISTS sim_run_id uuid REFERENCES sim_runs(id);
ALTER TABLE round_states              ADD COLUMN IF NOT EXISTS sim_run_id uuid REFERENCES sim_runs(id);
ALTER TABLE agent_decisions           ADD COLUMN IF NOT EXISTS sim_run_id uuid REFERENCES sim_runs(id);
ALTER TABLE agent_memories            ADD COLUMN IF NOT EXISTS sim_run_id uuid REFERENCES sim_runs(id);
ALTER TABLE covert_ops_log            ADD COLUMN IF NOT EXISTS sim_run_id uuid REFERENCES sim_runs(id);
ALTER TABLE exchange_transactions     ADD COLUMN IF NOT EXISTS sim_run_id uuid REFERENCES sim_runs(id);
ALTER TABLE agreements                ADD COLUMN IF NOT EXISTS sim_run_id uuid REFERENCES sim_runs(id);
ALTER TABLE observatory_events        ADD COLUMN IF NOT EXISTS sim_run_id uuid REFERENCES sim_runs(id);
ALTER TABLE observatory_combat_results ADD COLUMN IF NOT EXISTS sim_run_id uuid REFERENCES sim_runs(id);
ALTER TABLE pre_seeded_meetings       ADD COLUMN IF NOT EXISTS sim_run_id uuid REFERENCES sim_runs(id);

-- 1c. Backfill all existing rows to the legacy run
UPDATE country_states_per_round  SET sim_run_id = @legacy_run_id WHERE sim_run_id IS NULL;
-- … repeat for each of the 12 tables

-- 1d. Enforce NOT NULL + swap uniqueness keys
ALTER TABLE country_states_per_round  ALTER COLUMN sim_run_id SET NOT NULL;
-- … repeat

ALTER TABLE country_states_per_round
  DROP CONSTRAINT IF EXISTS country_states_per_round_scenario_round_country_key,
  ADD CONSTRAINT country_states_per_round_run_round_country_key
    UNIQUE (sim_run_id, round_num, country_code);
-- … repeat analogous uniqueness swaps for the other 11 tables

-- 1e. Drop the stop-gap test_runs table (M1-VIS metadata)
DROP TABLE IF EXISTS test_runs;
```

**Scenario_id is KEPT** on the hot tables (for now) as a redundant denorm for easy joins, but all reads/writes switch to `sim_run_id`. A later cleanup can drop `scenario_id` from these tables if desired.

### Step 2 — New service: `engine/services/sim_run_manager.py`

```python
def create_run(scenario_code: str, name: str, description: str | None = None,
               seed: int | None = None) -> str:
    """Create a new sim_run for the given scenario. Returns sim_run_id."""

def finalize_run(sim_run_id: str, status: str = 'completed',
                 notes: str | None = None) -> None:
    """Mark a run as finished. status: completed | visible_for_review | archived."""

def get_run(sim_run_id: str) -> dict: ...
def list_runs(scenario_code: str | None = None,
              status: str | None = None,
              limit: int = 50) -> list[dict]: ...
def seed_round_zero(sim_run_id: str) -> None:
    """Copy the scenario's R0 template state into the new run's R0 snapshot."""
```

`seed_round_zero` replaces the `_seed_round_from_r0` helper currently duplicated in L3 tests.

### Step 3 — Rewire every engine entry point from `scenario_code` to `sim_run_id`

**Files to update** (with rough signature change):

| File | Change |
|---|---|
| `engine/round_engine/resolve_round.py` | `resolve_round(scenario_code, round_num)` → `resolve_round(sim_run_id, round_num)` |
| `engine/services/budget_context.py` | same |
| `engine/services/tariff_context.py` | same |
| `engine/services/sanction_context.py` | same |
| `engine/services/opec_context.py` | same |
| `engine/services/movement_context.py` | same |
| `engine/services/movement_data.py` | (pure loader, no change) |
| `engine/round_engine/round_tick.py` | rewire to take sim_run_id |
| `engine/agents/full_round_runner.py` | rewire |
| `engine/agents/leader_round.py` | rewire |

Each file gets a small shim that accepts `sim_run_id`, looks up `scenario_id` once, and queries `*_per_round` tables by `sim_run_id` going forward.

**Validators are untouched** — they are pure functions that take dicts, not DB keys.

### Step 4 — Rewrite test fixtures

Every `conftest.py` / test that currently uses `scenario_code='start_one'` directly now does:

```python
@pytest.fixture
def sim_run(client):
    run_id = create_run(
        scenario_code='start_one',
        name=f"test_{request.node.name}",
        description=f"L{layer} test: {request.node.name}",
    )
    seed_round_zero(run_id)
    yield run_id
    # Test decides whether to finalize or archive via status update
```

Tests that want their run **left visible in Observatory**:

```python
finalize_run(run_id, status='visible_for_review',
             notes='M1 movement vertical slice — Columbia auto-embark demo')
```

No more round-200 hacks. Every test's rounds are 0..N and isolated.

### Step 5 — Observatory rewire

- `loadTestRuns()` → hits `/api/observatory/sim_runs?status=visible_for_review` (renamed from `/api/observatory/test_runs`)
- Response shape stays compatible: `{runs: [{id, name, scenario_code, round_start: 0, round_end: N, description}]}`
- Dropdown entries: `"M1 Movement · start_one · R0-1 · 2026-04-11 14:32"`
- Selection sets `state.simRunId = runs[i].id` (new state field) and all observatory API calls gain a `sim_run_id=` query param instead of (or alongside) `scenario=`.
- `/api/observatory/units`, `/countries`, `/events`, `/combats`, `/blockades`, `/global-series` all accept `sim_run_id` and filter by it.

### Step 6 — Delete `test_runs` table + its registry

- Drop `engine/services/test_run_registry.py`
- Remove the `/api/observatory/test_runs` route (replaced by `/sim_runs`)
- Remove the `register_test_run()` call from `test_movement_full_chain_ai.py` — finalize_run is enough.

### Step 7 — Green-test everything

Run in order:
1. **L1 suites** — validator tests are pure, should be unaffected. Confirm green.
2. **L2 persistence tests** — 4 economic + 1 movement. Each rewritten to create a run, exercise, finalize. Confirm green.
3. **L3 acceptance gates** — budget, tariffs, sanctions, OPEC, movement. Confirm green.
4. **Observatory smoke** — restart server, open dropdown, verify each visible run loads and renders maps/dashboards correctly.

---

## Risks & mitigations

| Risk | Mitigation |
|---|---|
| Backfill breaks existing round data | Legacy data lands in a single `legacy_start_one` archived run. Observatory filters it out by default. No deletes. |
| Missed call site (engine reads scenario_id somewhere I didn't catch) | Ripgrep sweep for `scenario_id` / `scenario_code` in all of `engine/` and `tests/`. Expected hit count: ~150. Each one audited by hand. |
| Tests slow down because each creates a run | Run creation is one INSERT. R0 seed copies ~345 units + 20 country rows. ~200ms per test. Acceptable. |
| Forgetting to finalize a run leaves garbage | conftest teardown auto-finalizes with `status='archived'` if test didn't do it explicitly. |

## Scope boundaries

**IN:** the 12 hot tables, their engine entry points, all slice tests, Observatory selector.
**OUT:**
- Dropping `scenario_id` column from hot tables (keep as denorm for now)
- Multi-run comparison UI (later — F2)
- Run seeding from arbitrary snapshots (later — F3)
- Human participant bindings to runs (next phase after UNMANNED SPACECRAFT)

---

## Execution order (when approved)

1. Apply schema migration (`sim_run_foundation_v1`) with backfill
2. Write `sim_run_manager.py` + L1 tests for it
3. Rewire `resolve_round` + verify budget L3 passes
4. Rewire remaining 3 economic context services + verify L3s pass
5. Rewire movement + verify L3 passes
6. Rewire Observatory API + JS
7. Delete `test_runs` table + registry
8. Final sweep, commit, `CHECKPOINT_F1_SIM_RUNS.md` written

**Green-light check after each numbered step.** Any regression stops the work and gets diagnosed before moving on.
