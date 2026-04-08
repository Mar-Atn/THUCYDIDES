# DB Cleanup Audit - 2026-04-08

**Agent:** QA | **Project:** lukcymegoldprbovglmn | **Time:** 2026-04-08

---

## Audit Results

### Configuration (PRESERVED - do not touch)

| Table | Rows | Status |
|---|---|---|
| sim_templates | 1 (`ttt_v1_0`) | Canonical. KEPT. |
| sim_scenarios | 1 (`start_one`) | Canonical. KEPT. |
| sim_runs | 1 (status: `setup`) | Single run. KEPT. |

### Per-Round State (PRESERVED)

| Table | R0 | R1 | R2 | Notes |
|---|---|---|---|---|
| country_states_per_round | 20 | 20 | 20 | R0 = canonical seed (Apr 5). R1-R2 = today's run. |
| unit_states_per_round | 345 | 345 | 345 | Same pattern. |
| global_state_per_round | 1 | 1 | 1 | Phantom R3-R6 already cleaned in prior session. |

### Run Data (PRESERVED)

| Table | R1 | R2 | Total | Run timestamp |
|---|---|---|---|---|
| agent_decisions | 59 | 59 | 118 | 15:19-15:28 UTC |
| observatory_events | 107 | 105 | 212 | 15:19-15:32 UTC |
| observatory_combat_results | 13 | 7 | 20 | 15:26-15:32 UTC |

All data from a single run today. No overlapping or duplicate runs detected.

### Empty Tables (no action needed)

- exchange_transactions: 0
- agreements: 0
- covert_ops_log: 0
- blockades: 0
- pre_seeded_meetings: 0

### Cleaned

| Table | Rows deleted | Reason |
|---|---|---|
| agent_memories | 75 | Cleared for clean next-run start. These regenerate automatically. Were all from today's run (R1: 7, R2: 68). |

### Not Found (good)

- No battery test leftovers (R89+): 0
- No orphaned records (all data tied to `start_one` scenario)
- No duplicate/test scenarios
- No stale data from prior sessions

---

## Verdict

**Database is CLEAN.** Only one meaningful cleanup action taken (agent_memories cleared). All canonical template/scenario/seed data preserved. All run data is from a single coherent run today -- no stale artifacts from prior test sessions.

### Post-Cleanup Row Counts

| Table | Rows |
|---|---|
| sim_templates | 1 |
| sim_scenarios | 1 |
| sim_runs | 1 |
| agent_decisions | 118 |
| observatory_events | 212 |
| country_states_per_round | 60 |
| unit_states_per_round | 1035 |
| global_state_per_round | 3 |
| observatory_combat_results | 20 |
| agent_memories | 0 |
| exchange_transactions | 0 |
| agreements | 0 |
| covert_ops_log | 0 |
| blockades | 0 |
| pre_seeded_meetings | 0 |
