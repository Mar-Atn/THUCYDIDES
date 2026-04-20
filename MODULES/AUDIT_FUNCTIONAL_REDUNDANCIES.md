# FUNCTIONAL AUDIT — Redundancies, Inconsistencies, Dead Code

**Date:** 2026-04-20
**Scope:** `/app/` codebase + Supabase DB (project `lukcymegoldprbovglmn`)
**Author:** Audit Agent (read-only, no code modified)

---

## 1. EXECUTIVE SUMMARY — Top 10 Issues by Severity

| # | Severity | Issue | Impact |
|---|----------|-------|--------|
| 1 | **CRITICAL** | 14 duplicate `_write_event()` functions across engine services | Maintenance nightmare, inconsistent signatures |
| 2 | **CRITICAL** | 13 duplicate `_get_scenario_id()` functions despite shared `common.py` | Same function reimplemented 13 times |
| 3 | **HIGH** | `_hex_distance()` duplicated in 5 files | Formula drift risk, already has naming variant `_hex_distance_v2` |
| 4 | **HIGH** | `MARTIAL_LAW_POOLS` defined in 3 separate files with same data | Config scattered, change = 3 edits |
| 5 | **HIGH** | `OPEC_MEMBERS` defined in 3 separate places | Sync risk (position_actions.py, opec_validator.py, full_round_runner.py) |
| 6 | **HIGH** | 7 deprecated files (4,500 lines) still imported by active code | stage*_test.py + round_engine/* still in dependency chain |
| 7 | **HIGH** | `country_code` vs `country_id` naming split across DB and code | 11 tables use `country_code`, 4 use `country_id` for same concept |
| 8 | **MEDIUM** | ParticipantDashboard.tsx is 7,108 lines — monolith component | Unmaintainable, 159 inline styles |
| 9 | **MEDIUM** | 10+ DB tables are empty AND unreferenced by any code | Dead schema: `ai_context`, `ai_contexts`, `ai_decisions`, `combat_results`, `events`, `facilitators`, `judgment_log` |
| 10 | **MEDIUM** | Deprecated DB columns still present in roles/countries tables | `ticking_clock`, `fatherland_appeal`, `personal_coins`, `political_support`, `dem_rep_split_*` |

---

## 2. DEAD CODE INVENTORY

### 2.1 Deprecated Files (marked DEPRECATED, still on disk)

| File | Lines | Status | Still Imported By |
|------|-------|--------|-------------------|
| `engine/agents/stage1_test.py` | 330 | DEPRECATED 2026-04-06 | Nobody |
| `engine/agents/stage2_test.py` | 389 | DEPRECATED 2026-04-06 | **stage3_test, stage4_test, stage5_test, full_round_runner, leader_round** |
| `engine/agents/stage3_test.py` | 415 | DEPRECATED 2026-04-06 | **stage4_test, stage5_test, leader_round** |
| `engine/agents/stage4_test.py` | 361 | DEPRECATED 2026-04-06 | **stage5_test, leader_round** |
| `engine/agents/stage5_test.py` | 467 | DEPRECATED 2026-04-06 | **leader_round** |
| `engine/round_engine/combat.py` | 398 | DEPRECATED 2026-04-06 | **test_combat.py, test_calibration_combat.py** |
| `engine/round_engine/rd.py` | 54 | DEPRECATED 2026-04-06 | **resolve_round.py** |

**Key problem:** `leader_round.py` (the canonical replacement) still imports `TOOL_SCHEMAS` from `stage3_test.py`, `COMMIT_ACTION_SCHEMA` from `stage4_test.py`, and functions from `stage5_test.py`. These constants need to be extracted to a non-deprecated module.

### 2.2 `resolve_round.py` — 2,087-line "deprecated" file still in active use

`engine/round_engine/resolve_round.py` is marked DEPRECATED but is imported by **29 test files** and by `full_round_runner.py`. It is the actual decision processor for combat, movement, sanctions, tariffs, budgets, OPEC, blockades, covert ops, nuclear, agreements, transactions, and more. This file is NOT actually deprecated — it is a core engine component that has not been replaced.

### 2.3 DB Tables: Empty AND Never Referenced in Code

| Table | Rows | Referenced in Code? |
|-------|------|-------------------|
| `ai_context` | 0 | NO |
| `ai_contexts` | 0 | NO |
| `ai_decisions` | 0 | NO |
| `argus_conversations` | 0 | NO |
| `argus_event_memory` | 0 | NO |
| `combat_results` | 0 | NO |
| `country_state` | 0 | NO (only in test variable names, not as DB table) |
| `events` | 0 | NO (replaced by `observatory_events`) |
| `facilitators` | 0 | NO |
| `judgment_log` | 0 | NO |
| `messages` | 0 | NO |
| `meetings` | 0 | NO |
| `pre_seeded_meetings` | 0 | NO |
| `role_state` | 0 | NO |

**14 orphan tables.** These appear to be design-phase placeholders that were never implemented, or were replaced by other tables (e.g., `events` replaced by `observatory_events`).

### 2.4 DB Tables: Empty But Referenced (runtime-populated)

| Table | Rows | Status |
|-------|------|--------|
| `run_roles` | 0 | **Code reads `roles` directly now.** run_roles table is vestigial. `seed_run_roles()` is a documented no-op. |
| `blockades` | 0 | Legitimately runtime-only. Code references extensively. |
| `basing_rights` | 0 | Legitimately runtime-only. |
| `pending_actions` | 0 | Runtime buffer. |
| `round_reports` | 0 | Written by `persistence.py` but never queried. |
| `power_assignments` | 0 | Written by `power_assignments.py`. |

### 2.5 Deprecated Functions in Active Code

| File:Line | Function | Note |
|-----------|----------|------|
| `change_leader.py:501` | `_migrate_hos_actions()` | DEPRECATED, use `recompute_role_actions()` |
| `political_validator.py:81,126` | Two validation functions | DEPRECATED, replaced by change_leader |
| `position_helpers.py:374` | `sync_legacy_booleans()` | DEPRECATED, will be removed when legacy columns drop |
| `action_schemas.py:152` | `ChangeLeaderOrder` schema | DEPRECATED, replaced by CONTRACT_CHANGE_LEADER |

---

## 3. NAMING INCONSISTENCIES

### 3.1 `country_code` vs `country_id` — The Split

**DB columns by naming convention:**

Using `country_code`:
- `agent_decisions`, `agent_memories`, `country_states_per_round`, `election_nominations`, `election_results`, `election_votes`, `layout_units`, `leadership_votes`, `nuclear_actions`, `observatory_events`, `pending_actions`, `power_assignments`, `run_roles`, `unit_states_per_round`

Using `country_id`:
- `country_state`, `deployments`, `messages`, `org_memberships`, `roles`

**In code:** Functions accept `country_code` as parameter name but query `country_id` columns:
- `movement_context.py`: parameter is `country_code`, queries `.eq("country_code", country_code)` on countries table (which has the column as `id`)
- `blockade_engine.py:25`: `.eq("country_id", country_code)` — mixing names in one line
- `run_roles.py:57-58`: returns BOTH `"country_code": r["country_id"]` AND `"country_id": r["country_id"]` for backward compatibility
- `transaction_engine.py:420`: `"country_code": d["country_id"]` — explicit mapping

**Relationships table:** Uses `from_country_id` / `to_country_id` (consistent with `_id` convention).

### 3.2 `position_type` vs `positions[]` — Dual System

The DB `roles` table has BOTH:
- `position_type` (single string: "head_of_state", "military", etc.)
- `positions` (array: ["head_of_state", "military"])

Code in `position_actions.py:253-286` has explicit DEPRECATED fallback logic that checks `is_head_of_state` boolean first, then `positions[]`, then `position_type`. Three systems for the same concept.

**Legacy boolean columns still in DB `roles` table:**
- `is_head_of_state` (boolean)
- `is_military_chief` (boolean)
- `is_diplomat` (boolean)
- `is_economy_officer` (boolean)

These are actively read by: `coup_engine.py:64`, `protest_engine.py:65,69,75`, `election_engine.py:511`, `change_leader.py:44,60,110`, `world_context.py:96`.

**`run_roles` table** has booleans but NO `positions[]` or `position_type` column.

### 3.3 `unit_code` vs `unit_id`

- DB `deployments` table column: `unit_id`
- In-code variable: `unit_code` (used extensively in combat/movement logic)
- Translation at call sites: `code = dep.get("unit_id") or dep["id"]` (action_dispatcher.py, appears 10+ times)

### 3.4 Action ID Inconsistencies Between Frontend and Backend

Actions in frontend `action_constants.ts` not in backend `ACTION_CATEGORIES` (main.py):
- `cast_vote` — in frontend, missing from backend categories
- `accept_meeting` — in frontend categories but only in REACTIVE_ACTIONS in backend

Actions in backend not in frontend:
- `meet_freely` — in backend categories but marked "Legacy" in frontend labels

---

## 4. DB TABLE AUDIT

### 4.1 Deprecated Columns (data confirms unused)

| Table | Column | Status | Evidence |
|-------|--------|--------|----------|
| `roles` | `ticking_clock` | All 200 rows NULL/empty | DEPRECATED 2026-04-17, cleared from DB |
| `roles` | `fatherland_appeal` | All 200 rows = 0/NULL | DEPRECATED 2026-04-17, scrapped mechanic |
| `roles` | `personal_coins` | 15 NULL, 185 have values | DEPRECATED 2026-04-15 (no personal transactions) but data exists |
| `countries` | `political_support` | Has values (not null) | DEPRECATED 2026-04-15 in code, but still has data |
| `countries` | `dem_rep_split_dem` | Has values | DEPRECATED 2026-04-15 (parliament simplified) |
| `countries` | `dem_rep_split_rep` | Has values | DEPRECATED 2026-04-15 |
| `deployments` | `zone_id` | All 1,363 rows NULL | DEPRECATED for positioning, hex coords are canonical |

### 4.2 Tables With No Foreign Keys (orphaned)

- `blockades` — no FK constraints (uses `sim_run_id`, `imposer_country_id` as plain text)
- `sim_config` — no FK constraints

### 4.3 Duplicate Table

`messages` exists in BOTH `public` and `realtime` schemas. The `public.messages` table has 0 rows and is never referenced in code. Likely a collision with Supabase Realtime's internal table.

---

## 5. DUPLICATE LOGIC

### 5.1 `_write_event()` — 14 Copies

A shared `write_event()` exists in `engine/services/common.py` and is used by 6 modules. But **14 other modules** define their own private `_write_event()` with slightly different signatures:

| File | Signature difference |
|------|---------------------|
| `agreement_engine.py` | `(client, sim_run_id, scenario_id, round_num, event_type, country_code, ...)` |
| `assassination_engine.py` | `(client, sim_run_id, scenario_id, round_num, country_code, event_type, ...)` — **swapped order** |
| `basing_rights_engine.py` | `(client, sim_run_id, round_num, country_code, ...)` — **no scenario_id** |
| `coup_engine.py` | `(client, sim_run_id, scenario_id, round_num, country_code, event_type, ...)` |
| `protest_engine.py` | same as coup |
| `run_roles.py` | `(client, sim_run_id, round_num, country_code, ...)` — **no scenario_id** |
| `power_assignments.py` | `(client, sim_run_id, round_num, country_code, ...)` — **no scenario_id** |
| `transaction_engine.py` | `(client, sim_run_id, scenario_id, round_num, event_type, country_code, ...)` — **event_type before country_code** |
| *...and 6 more* | Various orderings |

The parameter order inconsistency (`event_type` before vs after `country_code`) is a bug waiting to happen.

### 5.2 `_get_scenario_id()` — 13+ Copies

`common.py` provides `get_scenario_id(client, sim_run_id)`. But 13 engine services and 12 test files define their own `_get_scenario_id()`. The engine-service copies query `sim_runs` (by `sim_run_id`); the context-service copies query `sim_scenarios` (by `scenario_code`). Two genuinely different patterns, but the `sim_run_id` variant should use `common.py`.

### 5.3 `_hex_distance()` — 5 Copies

| File | Function Name |
|------|--------------|
| `naval_combat_validator.py:28` | `_hex_distance()` |
| `air_strike_validator.py:47` | `_hex_distance()` |
| `bombardment_validator.py:22` | `_hex_distance()` |
| `engines/military.py:2495` | `_hex_distance_v2()` |
| `round_engine/resolve_round.py:1790` | `_hex_distance()` |

All implement the same offset-coordinate hex distance formula. Should be a single utility.

### 5.4 `MARTIAL_LAW_POOLS` — 3 Copies

| File | Definition |
|------|-----------|
| `martial_law_engine.py:23` | `{"sarmatia": 10, "ruthenia": 6, "persia": 8, "cathay": 10}` |
| `domestic_validator.py:138` | `{"sarmatia": 10, "ruthenia": 6, "persia": 8, "cathay": 10}` |
| `resolve_round.py:1149` | `{"sarmatia": 10, "ruthenia": 6, "persia": 8, "cathay": 10}` |

### 5.5 `OPEC_MEMBERS` — 3 Copies

| File | Definition |
|------|-----------|
| `config/position_actions.py:117` | `{"caribe", "mirage", "persia", "sarmatia", "solaria"}` |
| `opec_validator.py:29` | `frozenset({"caribe", "mirage", "persia", "sarmatia", "solaria"})` |
| `full_round_runner.py:231` | `{"caribe", "mirage", "persia", "sarmatia", "solaria"}` |

`opec_validator.py:28` even has a comment: "Must be kept in sync with engine/agents/full_round_runner.py:OPEC_MEMBERS."

---

## 6. FRONTEND COMPONENT ANALYSIS

### 6.1 `ParticipantDashboard.tsx` — 7,108 Lines

This is a monolith. It contains:
- The main `ParticipantDashboard` component (~500 lines)
- `TabActions` sub-component (embedded, ~700 lines)
- Nuclear authorization/interception modals (embedded, ~200 lines with inline dark-theme styles)
- Action form components (embedded inline for each of ~25 action types)
- Country tab, World tab, Map tab, Confidential tab logic

**Inline styles:** 159 `style={{...}}` occurrences, primarily in nuclear-related components. These use hardcoded colors (`#FF3C14`, `#0A0E1A`) that should be Tailwind theme tokens.

**`className=` usages:** 1,257 (Tailwind). The codebase mixes Tailwind and inline styles inconsistently.

**`HEX_OWNERS` map** is hardcoded in this file (lines 20-39) — a 40-entry country-to-hex lookup that duplicates data from `map_config.py`.

### 6.2 Other Frontend Files

- `FacilitatorDashboard.tsx`: 2,160 lines — large but manageable
- `PublicScreen.tsx`: 936 lines — reasonable
- `ModeratorDashboard.tsx`: 267 lines — clean

### 6.3 No Frontend TODOs/DEPRECATEDs

Zero `TODO`, `DEPRECATED`, or `FIXME` markers in `.tsx` files.

---

## 7. CONFIGURATION SCATTERED INVENTORY

### 7.1 Probabilities Hardcoded in Engine Files

Every covert/political engine has its own module-level constants:

| Module | Constants |
|--------|----------|
| `propaganda_engine.py` | `SUCCESS_PROB=0.55, DETECTION_PROB=1.0, ATTRIBUTION_PROB=0.20` |
| `sabotage_engine.py` | `SUCCESS_PROB=0.50, DETECTION_PROB=1.0, ATTRIBUTION_PROB=0.50, MILITARY_DESTROY_PROB=0.50` |
| `election_meddling_engine.py` | `SUCCESS_PROB=0.40, DETECTION_PROB=0.45, ATTRIBUTION_PROB=0.50` |
| `assassination_engine.py` | `SUCCESS_PROB=0.20, ATTRIBUTION_PROB=0.50` |
| `coup_engine.py` | `BASE_PROB=0.15, PROTEST_BONUS=0.25, LOW_STABILITY_BONUS=0.15` |
| `nuclear_chain.py` | `NUCLEAR_HIT_PROB=0.80, TARGET_AD_INTERCEPT_PROB=0.50, LEADER_DEATH_PROB=1/6` |
| `engines/military.py` | `downed_prob=0.15`, missile probs 0.60/0.20, various inline |
| `combat_context.py` | `hit_prob=0.12`, `downed_prob=0.15` |

No centralized probability config file exists. Changing a probability requires finding the right engine file.

### 7.2 Country Lists

| List | Locations |
|------|-----------|
| OPEC members | 3 files (see 5.5) |
| Martial law eligible | 3 files (see 5.4), plus `position_actions.py:114` |
| Columbia election actions | `position_actions.py:120` |

### 7.3 `ACTION_CATEGORIES` — Backend vs Frontend

Backend (`main.py:1319`): flat dict `{action_type: category_string}`.
Frontend (`action_constants.ts:57`): grouped dict `{category_label: action_type[]}`.

These are different structures serving different purposes, but the action lists must be kept in sync manually. No automated cross-check exists.

---

## 8. RECOMMENDED CLEANUP PLAN

### Phase 1: Safe / Obvious (no behavior change)

1. **Delete 14 orphan DB tables** that have 0 rows and no code references:
   `ai_context`, `ai_contexts`, `ai_decisions`, `argus_conversations`, `argus_event_memory`, `combat_results`, `country_state`, `events`, `facilitators`, `judgment_log`, `messages` (public), `meetings`, `pre_seeded_meetings`, `role_state`

2. **Consolidate `_write_event()`** — migrate all 14 private copies to use `common.write_event()`. Requires normalizing the parameter order (recommend: `country_code` before `event_type` to match DB insert order).

3. **Consolidate `_get_scenario_id()`** — migrate the `sim_run_id`-based copies to use `common.get_scenario_id()`. Keep the `scenario_code`-based variant separate but named differently.

4. **Extract `hex_distance()` to a utility** — create `engine/services/hex_utils.py` with one canonical implementation. Update 5 files to import from there.

5. **Extract constants from deprecated stage*_test.py** — move `TOOL_SCHEMAS`, `COMMIT_ACTION_SCHEMA`, `load_hos_agents` to a non-deprecated module (e.g., `engine/agents/schemas.py`). Then `leader_round.py` and `full_round_runner.py` import from the new module.

6. **Centralize `MARTIAL_LAW_POOLS`** in `config/position_actions.py` (already has `MARTIAL_LAW_ELIGIBLE`). Import from there in `martial_law_engine.py`, `domestic_validator.py`, `resolve_round.py`.

7. **Centralize `OPEC_MEMBERS`** — single definition in `config/position_actions.py`. Import in `opec_validator.py` and `full_round_runner.py`.

8. **Drop deprecated DB columns** from roles: `ticking_clock` (all empty), `fatherland_appeal` (all zero). These are confirmed dead.

### Phase 2: Medium Risk (requires testing)

9. **Drop `zone_id` from deployments** — all 1,363 rows are NULL. Code has `DEPRECATED` comments. But some code still reads it as fallback.

10. **Unify `country_code`/`country_id` naming** — pick ONE convention for new code. Add a project rule to CLAUDE.md. Migrate incrementally (DB column renames are destructive).

11. **Remove legacy boolean columns** from roles (`is_head_of_state`, `is_military_chief`, `is_diplomat`, `is_economy_officer`) — but first audit all 20+ code paths that still read these booleans directly.

12. **Split `ParticipantDashboard.tsx`** into sub-components:
    - `NuclearModal.tsx` (~200 lines, all inline styles)
    - `TabActions.tsx` (already a function, just extract to file)
    - `ActionForms/` directory (one file per action type)
    - Convert inline styles to Tailwind classes

13. **Remove `run_roles` table** — it has 0 rows, `seed_run_roles()` is a no-op, and all code reads `roles` directly.

### Phase 3: Risky / Debatable (needs design decision)

14. **Resolve `resolve_round.py` status** — it is marked DEPRECATED but is the core engine. Either:
    - (a) Remove the DEPRECATED label and accept it as canonical, OR
    - (b) Actually migrate its 2,087 lines to `engines/*` modules and delete it

15. **Centralize probability config** — create `engine/config/probabilities.py` with all combat/covert/political probability constants. This is a design change that trades module isolation for central visibility.

16. **Delete deprecated files** (`stage1_test.py` through `stage5_test.py`, `round_engine/combat.py`, `round_engine/rd.py`) — but only after Phase 1 step 5 extracts the still-needed constants.

17. **Reconcile `ACTION_CATEGORIES`** between backend (main.py) and frontend (action_constants.ts) — consider generating one from the other, or a shared JSON source.

---

*End of audit. No code was modified.*
