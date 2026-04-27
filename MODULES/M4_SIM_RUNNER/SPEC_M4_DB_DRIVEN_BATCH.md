# SPEC: M4.x — DB-Driven Batch Decisions

**Version:** 1.0
**Date:** 2026-04-27
**Status:** APPROVED — building now
**Depends on:** M1 (Economic Engine), M4 (Sim Runner)

---

## 1. Problem

Batch decisions (budget, tariffs, sanctions, OPEC) flow through an in-memory `actions` dict during Phase B processing. This has two issues:

1. **Key mismatch bug:** `main.py` stores budgets as `actions["budget_decisions"]` but `economic.py` reads `actions["budgets"]`. Budgets silently ignored.
2. **Fragile architecture:** Data passes through memory between collection and engine execution. A server restart between collection and processing loses everything.

## 2. Solution: Write to DB at Submission Time

When a participant submits a batch decision during Phase A, write it immediately to `country_states_per_round` — the same table the engine already reads from.

```
BEFORE (broken):
  Submit → agent_decisions table → Phase B reads → builds actions dict → engine
  (key mismatch: budget_decisions ≠ budgets)

AFTER (systemic):
  Submit → agent_decisions table (audit trail)
       → country_states_per_round (engine reads directly)
  Phase B → engine reads from DB → no dict passing needed
```

## 3. Implementation

### 3.1 `_queue_batch_decision` — Write-Through to country_states_per_round

For each batch action type, write to the appropriate columns:

| Action | DB Columns on country_states_per_round |
|--------|---------------------------------------|
| `set_budget` | `budget_social_pct`, `budget_production`, `budget_research` |
| `set_tariffs` | Written to `tariffs` table directly (already exists) |
| `set_sanctions` | Written to `sanctions` table directly (already exists) |
| `set_opec` | `opec_production` |

### 3.2 Phase B Collection Simplified

`main.py` Phase B no longer needs to build the `actions` dict from `agent_decisions`. The engine reads everything from DB via `round_tick.py` (already implemented, line 308-370).

### 3.3 Verification

- Budget submission → check `country_states_per_round` has values
- Phase B runs → engine picks up values from DB
- No key mismatches possible — engine reads from canonical columns
