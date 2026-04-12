# CHECKPOINT — F1 Sim Run Foundation

**Date:** 2026-04-12 | **Status:** ✅ DONE | **Owner:** Marat + Build Team

> The 12 hot-path tables now key by `sim_run_id`. Lifecycle service shipped.
> Engine entry points dual-input compatible. Observatory rebuilt around
> `sim_runs`. The TTT data model finally matches the canonical Template /
> Scenario / Run taxonomy that CONCEPT and SEED have always assumed.

---

## What F1 changed

### 1. Schema migration `sim_run_foundation_v1`
- `sim_runs.status` enum extended: `+ archived, + visible_for_review`
- `sim_runs` lifecycle columns added: `description`, `seed`, `finalized_at`
- 12 hot-path tables gained `sim_run_id uuid NOT NULL REFERENCES sim_runs(id) ON DELETE CASCADE`
- 5 composite uniqueness constraints swapped from `(scenario_id, …)` to `(sim_run_id, …)`
- 6 new indexes on `(sim_run_id, round_num)`
- All pre-F1 rows backfilled into a single `archived` legacy run
  (`00000000-0000-0000-0000-000000000001`)
- `test_runs` stop-gap table dropped

### 2. New service `engine/services/sim_run_manager.py`
- `create_run(scenario_code, name, …) → sim_run_id`
- `seed_round_zero(sim_run_id)` — copies template R0 from legacy run
- `finalize_run(sim_run_id, status, notes)` — terminal state + timestamp
- `get_run(sim_run_id)` / `list_runs(scenario_code?, status?, limit)`
- `resolve_sim_run_id(uuid_or_code)` — dual-input resolver
- `get_scenario_id_for_run(sim_run_id)` — scenario lookup helper

### 3. Engine rewire (11 files, all dual-input)
- `engine/round_engine/resolve_round.py` (1811 lines, 22 inline event dicts updated, 5 helper signatures threaded with `sim_run_id`)
- `engine/engines/round_tick.py` — entry point + 5 helpers
- `engine/services/budget_context.py`, `tariff_context.py`, `sanction_context.py`, `opec_context.py`, `movement_context.py` — `_load_snapshot` and friends
- `engine/agents/full_round_runner.py` — `_emit_event`, `_load_current_economic_state`, `_load_situation_context`, mandatory decisions, transactions, `_persist_transaction_state_changes`
- `engine/agents/leader_round.py` — `_get_events_affecting_country`
- `engine/agents/tools.py` — `_load_live_units`, `_load_live_country_state`, `commit_action`, `read_memory`, `list_my_memories`, `write_memory`

All entry points accept either a `sim_run_id` UUID or a `scenario_code` string. A scenario code resolves to its archived legacy run (preserving pre-F1 behavior). New code can pass explicit run ids for isolation.

### 4. Observatory rebuilt around `sim_runs`
- New `/api/observatory/sim_runs` endpoint listing runs with status `visible_for_review` or `archived`, enriched with `scenario_code`
- All 6 data endpoints (`units`, `countries`, `events`, `combats`, `blockades`, `global-series`) accept optional `sim_run_id` query param and filter by it
- New `_resolve_observatory_run` helper applies the dual-input rule
- `observatory.js` state object carries `simRunId`; selector pins it; "live" mode clears it
- Selector dropdown labels: `"name · R0–N · scenario · status"`
- Old `/api/observatory/test_runs` removed (404), `engine/services/test_run_registry.py` deleted

### 5. Test fixtures
- New `tests/_sim_run_helper.py` with `legacy_run_id()` + `create_isolated_run()`
- New L2 suite `tests/layer2/test_sim_run_manager.py` (9 tests, full lifecycle round-trip)
- Temporary DB default `sim_run_id DEFAULT '00000000-0000-0000-0000-000000000001'` applied to all 12 hot tables (via `sim_run_id_temporary_default` migration) so pre-F1 fixtures that insert without specifying `sim_run_id` still work. **To be dropped in F1.1** after every test migrates to `create_isolated_run()`.

---

## Bugs caught and fixed during F1

| # | Bug | Cause | Fix |
|---|---|---|---|
| 1 | `_load_decisions` returned rows in non-deterministic order, breaking last-submission-wins | F1 swapped uniqueness constraint to `sim_run_id`, changing physical row placement; existing implicit ordering depended on the old constraint | Added explicit `ORDER BY created_at ASC` |
| 2 | `seed_round_zero(sim_run_id, source_run_id=run_id)` allowed self-source | Validation lived inside the `if source_run_id is None:` branch and was skipped when caller passed an explicit value | Moved the self-source check outside the `is None` branch |
| 3 | F1 demo run smoke test polluted R0 with duplicate country/unit rows under a second `sim_run_id` | Smoke test created a `visible_for_review` run, seeded R0, never cleaned up. `_seed_round_from_r0` test helpers query by `scenario_id` and pull all matching rows including duplicates | Cascade-deleted the demo run; documented as F1.1 cleanup item to migrate `_seed_round_from_r0` to query by `sim_run_id` |
| 4 | Pre-existing sanction state pollution: `cathay → sarmatia` was at level −3 instead of expected −1 | Older test runs over-wrote the row with stale data; pre-F1 model couldn't isolate runs | Updated the row directly to L−1; F1.1 will move L2 sanction tests to fresh runs |

---

## Test coverage at F1 close

| Layer | Suite | Result |
|---|---|---|
| L1 | All formula validators (excluding `test_foundation.py` which needs fastapi, unrelated) | **458 / 458 ✅** |
| L2 | `test_sim_run_manager.py` (lifecycle: create, seed, finalize, list, cascade delete) | 9 / 9 ✅ |
| L2 | `test_budget_persistence.py` | 4 / 4 ✅ |
| L2 | `test_tariff_persistence.py` | 7 / 7 ✅ |
| L2 | `test_sanction_persistence.py` | 7 / 7 ✅ |
| L2 | `test_opec_persistence.py` | 5 / 5 ✅ |
| L2 | `test_movement_persistence.py` | 7 / 7 ✅ |
| L2 | `test_budget_context.py` | 8 / 8 ✅ |
| L2 | `test_tariff_context.py` | 6 / 6 ✅ |
| L2 | `test_sanction_context.py` | 7 / 7 ✅ |
| L2 | `test_opec_context.py` | 7 / 7 ✅ |
| L2 | `test_movement_context.py` | 2 / 2 ✅ |
| **L2 total** | **11 suites, 69 tests** | **69 / 69 ✅** |
| L3 | `test_budget_full_chain_ai.py` (Gemini AI → context → validator → resolve_round → snapshot) | 1 / 1 ✅ |

(L3 tariff, sanction, opec, movement full-chain tests will rerun in the upcoming clean re-test pass before M2.)

---

## Live verification

Backend:
```
$ curl -s http://localhost:8888/api/observatory/sim_runs
{"runs": [{"id": "00000000-0000-0000-0000-000000000001",
           "name": "Thucydides Trap — Default Session",
           "status": "archived",
           "current_round": 8,
           "max_rounds": 8,
           "scenario_code": "start_one"}],
 "source": "db"}

$ curl -s "http://localhost:8888/api/observatory/countries?round=0&scenario=start_one&sim_run_id=00000000-0000-0000-0000-000000000001"
→ 20 country rows from db

$ curl -s "http://localhost:8888/api/observatory/units?round=0&scenario=start_one&sim_run_id=00000000-0000-0000-0000-000000000001"
→ 345 unit rows from db
```

Frontend:
- Top-bar **Test Run** dropdown shows the legacy archived run as the only entry (other runs will appear as the next phase registers visible test demos)
- Selecting it pins `state.simRunId` and re-fetches all data filtered by that run
- "— live —" clears the pin and reverts to the default scenario flow

---

## Files inventory

### New
| Path | Purpose |
|---|---|
| `app/engine/services/sim_run_manager.py` | Lifecycle service |
| `app/tests/_sim_run_helper.py` | Test helpers (legacy + isolated) |
| `app/tests/layer2/test_sim_run_manager.py` | 9 lifecycle tests |
| `PHASES/UNMANNED_SPACECRAFT/PLAN_F1_SIM_RUNS.md` | Execution plan |
| `PHASES/UNMANNED_SPACECRAFT/F1_TAXONOMY.md` | Canonical 3-level model spec for upward reconciliation |
| `PHASES/UNMANNED_SPACECRAFT/CHECKPOINT_F1_SIM_RUNS.md` | This document |

### Modified
| Path | Reason |
|---|---|
| `app/engine/round_engine/resolve_round.py` | Internal queries flipped to `sim_run_id`, helper signatures threaded |
| `app/engine/engines/round_tick.py` | Entry point + helpers |
| `app/engine/services/{budget,tariff,sanction,opec,movement}_context.py` | `_load_snapshot` keyed by `sim_run_id` |
| `app/engine/agents/full_round_runner.py` | All DB write sites flipped |
| `app/engine/agents/leader_round.py` | Event lookup |
| `app/engine/agents/tools.py` | Live state lookups + memory writes |
| `app/test-interface/server.py` | Observatory API endpoints + selector |
| `app/test-interface/static/observatory.js` | Selector logic + state |
| `app/test-interface/templates/observatory.html` | Top-bar dropdown |
| `app/tests/layer2/test_budget_context.py` | Helper updated to use `legacy_run_id()` |
| `app/tests/layer3/test_movement_full_chain_ai.py` | Removed deleted `register_test_run` call |

### Deleted
| Path | Why |
|---|---|
| `app/engine/services/test_run_registry.py` | Superseded by `sim_run_manager` |

### DB migrations
| Name | Effect |
|---|---|
| `sim_run_foundation_v1` | Schema change with backfill |
| `sim_run_id_temporary_default` | Adds DB default to unblock pre-F1 fixtures (drop in F1.1) |

---

## Open items deferred to F1.1

These are tracked in `F1_TAXONOMY.md` for the eventual cleanup sprint:

1. Migrate every L2/L3 slice test to `create_isolated_run()` for true per-test isolation, then drop the temporary DB default
2. Drop the redundant `scenario_id` denorm column from the 12 hot tables
3. Build a scenario authoring API parallel to `create_run`
4. Decide whether to widen `sim_runs.current_round <= 8` CHECK
5. Cross-LLM run comparison UI
6. Migrate `_seed_round_from_r0` test helpers to query by `sim_run_id` (prevents pollution like the F1 demo run incident)

---

## What this unblocks

Now that the substrate is clean, we can:

1. Run **multiple test variants of the same action** without trampling each other (the M1 Visible Demos task — multiple movement scenarios on the Observatory map)
2. Run **calibration sweeps** that need dozens of independent playthroughs of the same scenario
3. Build the **next military slices** (M2-M6) on a substrate where each combat scenario is genuinely isolated
4. Eventually plug in **human participants** without rework — the run lifecycle is the same whether AI or human drives it

## What comes next (per Marat 2026-04-12)

1. ✅ Document the new model — `F1_TAXONOMY.md` written
2. 🟡 Practical movement tests with multiple visible scenarios on the Observatory map
3. 🟡 Clean re-test of all 5 delivered actions on the new model (verify, polish)
4. ⬜ M2 ground combat slice
