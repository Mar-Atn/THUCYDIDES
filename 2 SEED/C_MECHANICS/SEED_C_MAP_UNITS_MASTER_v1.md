# SEED C — Map + Units Master Integration

**Version:** 1.1 | **Date:** 2026-04-13 | **Status:** Template v1.0 LOCKED
**Owner:** Marat Atn | **Phase:** BUILD — reconciled with F1_TAXONOMY.md + DET_F_SCENARIO_CONFIG_SCHEMA.md

---

## Purpose

Single authoritative source for the TTT map system, unit data model, placement mechanics, and template architecture. All other map/units SEED documents reference this one. Where a prior document (pre Template v1.0) contradicts this file, **this file wins**; legacy docs should be read as history, not current spec.

This document locks five things:
1. The shape of the map system (global + theaters + chokepoints).
2. The coordinate convention used everywhere.
3. The canonical theater↔global linkage mapping.
4. The unit data model (pure coordinate schema, 11 columns).
5. The Template → Scenario → Run hierarchy for maps and units.

---

## 1. Map System

### 1.1 Global map

- **Grid:** 10 rows × 20 cols, pointy-top hexagons, odd-row offset.
- **Coordinate space:** `(global_row, global_col)` with `global_row ∈ [1,10]`, `global_col ∈ [1,20]`.
- **Countries on global:** 22 land countries + sea. See `2 SEED/C_MECHANICS/C1_MAP/SEED_C1_MAP_GLOBAL_STATE_v4.json` for the authoritative per-hex ownership layout and `SEED_C1_MAP_STRUCTURE_v4.md` for the land-hex registry.
- **Water:** every non-land hex is a valid naval position. No named sea zones.
- **Die Hard hexes:** marked in the global JSON (currently: Ruthenia Fortress Belt zone). Die Hard flags are a global-level property that theater views inherit.

### 1.2 Theater maps

Two detailed theater maps in play at Template v1.0:

| Theater | Grid | Countries present | Purpose |
|---|---|---|---|
| **Eastern Ereb** | 10 × 10 | Sarmatia, Ruthenia, sea | Sarmatia-Ruthenia front. Active at start. |
| **Mashriq** | 10 × 10 | Persia, Solaria, Mirage, Phrygia, sea | Persia war (blockade + air + ground invasion). Active at start. |

Other tactical theaters (Formosa, Caribbean, Thule, Korea) resolve at global-hex level and do not have dedicated 10×10 maps in Template v1.0.

Per-theater hex ownership lives in:
- `2 SEED/C_MECHANICS/C1_MAP/SEED_C3_THEATER_EASTERN_EREB_STATE_v3.json`
- `2 SEED/C_MECHANICS/C1_MAP/SEED_C3_THEATER_MASHRIQ_STATE_v1.json`

Each theater cell carries `owner` and optionally `occupied_by` (another country's control of the cell). A cell may NOT be `occupied_by` its own owner — that is a data bug (one was fixed in Eastern Ereb at theater (5,8) on 2026-04-05; see §7.2).

### 1.3 Chokepoints

Chokepoints are specific water hexes with blockade mechanics. Template v1.0:

| Name | global_row | global_col |
|---|:---:|:---:|
| Caribe Passage | 8 | 4 |
| Formosa Strait | 7 | 17 |
| Gulf Gate | 8 | 12 |

Gulf Gate also serves as the Mashriq theater-link for sea cells in rows 7-10 of the theater (see §1.5).

### 1.3a Nuclear site hexes (added 2026-04-08)

Physical map locations of nuclear programs that can be targeted/destroyed:

| Country | global_row | global_col | Notes |
|---|:---:|:---:|---|
| Persia | 7 | 13 | Enrichment facility on Mashriq theater-link hex |
| Choson | 3 | 18 | Nuclear complex on global map (no theater) |

Other nuclear-armed countries (Columbia, Sarmatia, Cathay, Gallia, Albion) have abstract nuclear capability — no single targetable hex on the map.

**Canonical storage:** `sim_templates.map_config.nuclear_sites` (JSONB in DB) + `app/engine/config/map_config.py::NUCLEAR_SITES`.

### 1.4 Coordinate convention (LOCKED)

**`(row, col)` — row first, col second. Both 1-indexed.**

- `row` = vertical position measured from top (1 = top row, 10 = bottom row).
- `col` = horizontal position measured from left (1 = leftmost).
- Global map: `row ∈ [1,10]`, `col ∈ [1,20]`.
- Theater maps: `row ∈ [1,10]`, `col ∈ [1,10]`.

This applies **everywhere**: units CSV columns, API payloads, prompt contexts, map renderer helpers, SEED tables. The only place where legacy `(col,row)` still appears is in unmodified fields inside frozen theater JSONs (`global_link` string values in the Eastern Ereb JSON still read `"col,row"` — the viewer flips them on read). All NEW data written to disk uses `(row,col)`.

### 1.5 Theater ↔ global linkage (canonical, Marat-approved 2026-04-05)

Every theater cell aggregates up to exactly one global hex. This mapping is **part of the Template** — changing it means a new Template version (see §5.5).

#### Eastern Ereb → global

| Theater cell condition | Global hex (row, col) |
|---|:---:|
| `owner = sarmatia`, theater row 1-4 | (3, 12) |
| `owner = sarmatia`, theater row 5+ | (4, 12) |
| `owner = ruthenia` (any row, free or occupied) | (4, 11) |
| `owner = sea` (any) | (5, 12) |

#### Mashriq → global

| Theater cell condition | Global hex (row, col) |
|---|:---:|
| `owner = phrygia` | (6, 11) |
| `owner = solaria` | (7, 11) |
| `owner = mirage` | (8, 11) |
| `owner = persia`, theater row 1-3 | (6, 12) |
| `owner = persia`, theater row 4-6 | (7, 13) |
| `owner = persia`, theater row 7-10 | (8, 13) |
| `owner = sea`, theater row 3-6 | (7, 12) |
| `owner = sea`, theater row 7-10 | (8, 12) |

**Canonical implementation:** `app/test-interface/static/map.js::globalHexForTheaterCell()`. `units.csv` global coords are derived from theater coords via this table for every unit that carries a theater position.

---

## 2. Unit Data Model

The full formal schema lives in `2 SEED/D_ENGINES/SEED_D_UNIT_DATA_MODEL_v1.md`. This section is a summary.

### 2.1 Schema — 11 fields

| # | Field | Type | Required | Notes |
|:--:|---|---|:--:|---|
| 1 | `unit_id` | string | yes | Unique. Convention: `{country3}_{type1}_{seq}`, e.g. `col_g_01`, `per_d_03`, `sar_g_r1`. |
| 2 | `country_id` | string | yes | Owner country (matches `countries.csv`). |
| 3 | `unit_type` | enum | yes | `ground` \| `tactical_air` \| `strategic_missile` \| `air_defense` \| `naval`. |
| 4 | `global_row` | int | conditional | 1-10. Required if `status=active`. |
| 5 | `global_col` | int | conditional | 1-20. Required if `status=active`. |
| 6 | `theater` | enum | conditional | `''` \| `eastern_ereb` \| `mashriq`. Required when the unit sits on a theater-link global hex AND the unit is non-naval. |
| 7 | `theater_row` | int | conditional | 1-10. Required if `theater` set. |
| 8 | `theater_col` | int | conditional | 1-10. Required if `theater` set. |
| 9 | `embarked_on` | string | conditional | Another unit's `unit_id` (a naval carrier). Required iff `status=embarked`. |
| 10 | `status` | enum | yes | `active` \| `reserve` \| `embarked` \| `destroyed`. |
| 11 | `notes` | string | no | Human description. |

### 2.2 Status lifecycle

```
reserve ──place──► active ──pick-up──► reserve
                      │
                      ├──board-ship──► embarked
                      │                   │
                      │                   └──disembark──► active
                      │
                      └──────damage/loss──────► destroyed (terminal, audit-only)
```

### 2.3 Embarkation

- `embarked_on` references a naval unit's `unit_id` (the carrier).
- Embarked units have ALL coord fields empty; they inherit the carrier's position.
- Only land/air units embark on own-country naval units. No foreign embarkation in Template v1.0.
- Current Template v1.0: 6 embarked (4 tactical air, 2 ground).

### 2.4 Validation rules (see SEED_D for full list)

**Hard (block):**
- `status=active` → global_row AND global_col populated, in-bounds.
- `status=reserve` → all coord fields AND `embarked_on` empty.
- `status=embarked` → `embarked_on` set, coord fields empty.
- If `theater` is set, it must match a theater-link hex per §1.5, and theater coords must be in `[1,10]×[1,10]`.
- Non-naval unit whose active global hex is a theater-link hex → must have a theater cell.
- Naval unit → must be on a water hex (never carries theater coords).

**Soft (warning only):**
- Ground/air unit on foreign-country territory (allowed with basing rights).
- Unit on enemy-occupied hex without accompanying friendly force.

---

## 3. Placement Rules

### 3.1 Theater-link constraint

If a unit's global hex is one of the theater-link hexes listed in §1.5, and the unit is non-naval, the unit MUST carry matching `theater`, `theater_row`, `theater_col` fields. This prevents "ghost" units that appear on global-view but have no theater-view cell.

Conversely: a unit MAY only carry theater coords if its global coords resolve to a theater-link hex for that theater. The two must be mutually consistent.

### 3.2 Sea vs land

- `ground`, `air_defense`, `strategic_missile`, `tactical_air` must sit on a land hex OR be `embarked` on a naval unit.
- `naval` units must sit on a water/sea hex.
- Sea-link theater cells (Eastern Ereb sea → global (5,12); Mashriq sea rows 3-6 → (7,12); Mashriq sea rows 7-10 → (8,12)) accept naval placement only; those naval units do not carry theater cell coords.

### 3.3 Own-country ship embarkation

Tactical air and ground units may be embarked on naval units belonging to the same country (`country_id` matches the carrier's `country_id`). No cross-country embarkation in Template v1.0.

### 3.4 Occupied territory

A theater cell with `owner=X, occupied_by=Y` is Y-controlled territory. Y may place units there. X may still place units there (contested — soft warning, valid placement).

A cell's `occupied_by` MUST differ from its `owner`. Self-occupation is a data bug.

### 3.5 Country basing rights (soft)

At Template v1.0, cross-country basing is handled as a soft warning in the editor rather than a hard constraint, because the rules are relationship-dependent (Columbia stations forces in allied territories; Sarmatia does not station forces in free Ruthenia). Per-country basing policy is encoded in force structure discipline (see §6) and enforced by QA review, not by schema-level validation.

---

## 4. Aggregation & Display

### 4.1 Aggregation rule

For the **global view**: a country's units on a given global hex are the union of
- all units with that `(global_row, global_col)` and no theater set, PLUS
- all units with that `(global_row, global_col)` via theater-link (i.e. units sitting on theater cells that link to that global hex).

For the **theater view**: only units with the matching `theater` field, keyed by `(theater_row, theater_col)`.

### 4.2 Global view rendering

- Each hex shows per-country unit icons.
- Compact batching kicks in at 6+ units per hex (count badge replaces individual icons).
- Deterministic jitter avoids icon overlap.

### 4.3 Theater view

- Shows cell-level detail for every unit on that theater's cells.
- Theater-link global hexes carry a "drill-down" badge on the global view.

---

## 5. Template / Scenario / Run Architecture (CANONICAL as of 2026-04-05)

### 5.0 Principle: Sparse Override

A SCENARIO is a **"modified copy of TEMPLATE" with sparse overrides.** Every scenario field defaults to its template value. Scenarios store only the fields they want to change. Runtime access falls back to the template whenever a scenario field is unset.

This sparse-override model keeps calibration intact (formula coefficients are template-locked), minimises data duplication (a scenario is typically a handful of deltas), and makes facilitator customization auditable (the diff between template and scenario is explicit).

### 5.1 Hierarchy

```
🏛️ SIM TEMPLATE (master — evolves on month timescale; semver-tracked)
  │     Frozen per version. Owns all canonical defaults.
  ├── MAP SYSTEM
  │     ├── Global map (hex ownership, chokepoints, Die Hard markers)
  │     ├── Theater maps (Eastern Ereb, Mashriq)
  │     └── Theater↔global linkage (canonical table §1.5)
  ├── COUNTRY MASTER (stats, force structure, formula coefficients)
  ├── ROLE LIBRARY (briefings, personas, character sheets — defaults)
  ├── DEFAULT RELATIONSHIP MATRIX (bilateral tension, alliance, tariff, sanction)
  ├── DEFAULT UNIT LAYOUT (canonical starting placement)
  └── ALLOWED RANGES (round count, oil price, theater set)
        │
        ▼
🎬 SIM SCENARIO (one event's configuration — sparse override of one TEMPLATE)
  │     References template_id. Stores only deltas + scenario-owned fields.
  ├── Scenario-OWNED (no template default exists)
  │     Event metadata, SIM starting date, max rounds, oil price start,
  │     Phase A duration, active theaters, role assignments, election
  │     schedule, scripted event timeline.
  └── Scenario OVERRIDES (sparse; fall back to template if unset)
        country_stat_overrides, relationship_overrides,
        role_briefing_overrides, role_persona_overrides, unit_layout_id.
        │
        ▼
⚡ SIM-RUN (one actual playthrough — immutable once started)
        Frozen snapshot of merged (template + scenario) config at run start.
        Append-only event log, per-round world/country snapshots,
        user↔role bindings, per-role per-run agent memories.
```

### 5.2 TEMPLATE

Identity: `id, code, name, version, description, created_at`. Versioned via semver + name (e.g. v1.0 "Power Transition 2026"). Multiple templates coexist in the DB; scenarios reference a specific `template_id`. Frozen per version — advancing the version implies all scenarios must explicitly migrate.

Template owns the canonical defaults:
- **Map topology** (hexes, adjacency, theaters, chokepoints, Die Hard markers) — see `SEED_C1_MAP_GLOBAL_STATE_v4.json`, `SEED_C3_THEATER_*_STATE_*.json`.
- **Country master list** + starting stats (GDP, inflation, treasury, military, tech, stability) — see `C4_DATA/countries.csv`.
- **Role library** + character sheets / personas / briefings (default set).
- **Action catalog** (referenced — code-backed; see §5.5).
- **Formula coefficients** (per-country, **LOCKED** — scenarios cannot override).
- **Default relationship matrix** (bilateral tension / alliance / tariff / sanction).
- **Default unit layout** — `C4_DATA/units.csv` (345 units at v1.0).
- **Allowed round-count range** (e.g. [6, 8]).
- **Allowed oil-price range** (e.g. [50, 150]).
- **Allowed theater set** (which theaters can be activated by a scenario).

### 5.3 SCENARIO

Identity: `id, template_id (FK), code, name, event_name, event_date, created_at`. Two categories of fields: **scenario-OWNED** (no template default) and **scenario OVERRIDES** (sparse, fall back to template).

**Scenario-OWNED fields (no template default):**
- **Event metadata:** venue, facilitator_ids, participant_count, participant_profile, delivery_format, learning_objectives.
- **SIM starting date** (in-fiction time, e.g. "Q1 2026").
- **Max rounds chosen** (must lie in template's allowed range).
- **Oil price starting value** (must lie in template's allowed range).
- **Phase A duration override.**
- **Active theaters** (subset of template's allowed theater set that are ON for this scenario).
- **Role assignments** (which of template's roles are active + who plays what).
- **Election schedule** (round numbers per election type).
- **Scripted event timeline** (mandatory events per round, e.g. org meetings).

**Scenario OVERRIDES (sparse — unset fields fall back to template):**
- `country_stat_overrides` JSONB: `{country_code: {gdp: 285, ...}}` — only the changed fields.
- `relationship_overrides` JSONB: bilateral tension / alliance / tariff / sanction deltas.
- `role_briefing_overrides` JSONB: per-role briefing additions or modifications.
- `role_persona_overrides` JSONB: per-role persona modifications.
- `unit_layout_id` FK: pointer to a saved units layout (NULL = use template's default layout).

**Template-LOCKED (scenarios CANNOT override):**
- Formula coefficients (preserves calibration across scenarios).
- Map topology (hexes, adjacency, linkage).
- Action catalog.
- Engine architecture / cognitive blocks / round phases.

### 5.4 SIM-RUN

Identity: `id, scenario_id (FK), status, started_at, completed_at`. An immutable playthrough. At run start, the engine resolves the scenario (template + sparse overrides) into a complete frozen config snapshot stored in `run_config` JSONB.

Contains:
- Frozen snapshot of the merged (template + scenario) config.
- User ↔ role bindings.
- Per-round immutable world-state snapshots.
- Per-round immutable country-state snapshots.
- Append-only event log (the behavioral truth).
- Per-role, per-run agent memories.
- All action submissions, relationship changes, combat outcomes.

### 5.5 Web App — hard-coded boundary

These live in code, not data. Changing them requires a code release, not a template/scenario edit:
- Engine implementations (parameters flow from template).
- Action catalog (code-backed; adding actions = code change).
- Event type taxonomy.
- 4-block cognitive architecture.
- Round phase structure (Phase A / Phase B).
- UI layouts, Realtime, Auth, API.

### 5.6 Decision log

12 decisions locked by Marat on 2026-04-05 (see `CONCEPT TEST/CHANGES_LOG.md` — "SCENARIO TAXONOMY LOCKED" section).

Full canonical spec (schema, JSONB shapes, validation rules, examples): `3 DETAILED DESIGN/DET_F_SCENARIO_CONFIG_SCHEMA.md`.

DB schema additions: `3 DETAILED DESIGN/DET_B1a_TEMPLATE_TAXONOMY.sql`.

Seed SQL: `CONCEPT TEST/template_v1_0_seed.sql`, `CONCEPT TEST/scenario_start_one_seed.sql`.

### 5.7 Versioning: map changes → new Template

The following count as map changes and therefore force a new Template version:
1. Adding/removing hexes from the global or theater maps.
2. Changing hex ownership.
3. Changing any row of the theater↔global linkage table (§1.5).
4. Adding/removing chokepoints or Die Hard markers.

When a Template version advances, all saved scenario layouts from the old Template remain pinned to their original coords unless explicitly re-saved under the new Template by a moderator.

---

## 5a. Bilateral Relationship Model — 8 States (added 2026-04-08)

Every pair of countries has a bilateral relationship tracked in the `relationships` table with two columns:

- **`relationship`** — the STARTING/REFERENCE value, frozen per template. Uses legacy labels from CSV (`alliance`, `close_ally`, `friendly`, `neutral`, `tense`, `hostile`, `at_war`, `strategic_rival`).
- **`status`** — the LIVE engine state, updated during play. Uses the canonical 8-state model below.

### Canonical 8-State Model

| State | Meaning | Transitions |
|---|---|---|
| **allied** | Formal alliance, mutual defense commitment | → friendly (alliance dissolved) |
| **friendly** | Positive relations, cooperation, no formal treaty | → allied (treaty signed), → neutral (drift) |
| **neutral** | No strong alignment either way | → friendly (cooperation), → tense (friction) |
| **tense** | Friction, diplomatic pressure, not hostile | → hostile (escalation), → neutral (de-escalation) |
| **hostile** | Active antagonism, sanctions, not shooting | → military_conflict (attack), → tense (de-escalation) |
| **military_conflict** | Active combat — STICKY, does not auto-resolve | → armistice (ceasefire signed), → peace (treaty signed) ONLY |
| **armistice** | Ceasefire signed, combat stopped, territory frozen | → peace (treaty), → military_conflict (breach) |
| **peace** | War formally ended via peace treaty | → friendly (over time), → neutral |

### Key Rules

1. **`military_conflict` is STICKY** — only transitions via signed agreement (armistice or peace treaty). No automatic cooling. No time-based decay.
2. **Breach of armistice** (attacking after signing) → automatic return to `military_conflict` + all countries notified.
3. **War is DETECTED, not declared** — if country A attacks country B, status becomes `military_conflict`. Public war declarations are political theater, not a game mechanic.
4. Engine reads `status` column for all war/peace checks. The `relationship` column is preserved as the template starting point for reference and resets.

### Mapping: `relationship` → initial `status`

| `relationship` (template/CSV) | → initial `status` |
|---|---|
| `alliance`, `close_ally` | `allied` |
| `friendly` | `friendly` |
| `neutral` | `neutral` |
| `tense` | `tense` |
| `hostile`, `strategic_rival` | `hostile` |
| `at_war` | `military_conflict` |

---

## 6. Q1 2026 Canonical Starting Conditions

### 6.0 Authority chain (locked 2026-04-05)

```
start_one.csv (moderator hand-reviewed)  →  CANONICAL
        ↓
units.csv (engine default, identical snapshot at lock-time)
        ↓
countries.csv mil_* columns (DERIVED aggregate summary)
```

`start_one.csv` is the canonical Template v1.0 default unit placement AND force structure. All divergences must be resolved in favor of `start_one.csv`. `countries.csv` mil_* values are a derived cache, not independent truth.

### 6.1 Force structure (Template v1.0, 345 units total)

Per-country totals (ground / tactical_air / strategic_missile / air_defense / naval):

| Country | G | A | M | D | N |
|---|:--:|:--:|:--:|:--:|:--:|
| Columbia | 22 | 15 | 12 | 6 | 11 |
| Cathay | 25 | 12 | 4 | 3 | 7 |
| Sarmatia | 18 | 8 | 12 | 3 | 2 |
| Ruthenia | 11 | 3 | 0 | 1 | 0 |
| Persia | 8 | 6 | 0 | 1 | 0 |
| Gallia | 6 | 4 | 2 | 1 | 1 |
| Teutonia | 6 | 3 | 0 | 1 | 0 |
| Freeland | 5 | 2 | 0 | 1 | 0 |
| Ponte | 4 | 2 | 0 | 0 | 0 |
| Albion | 4 | 3 | 2 | 2 | 2 |
| Bharata | 12 | 4 | 0 | 2 | 2 |
| Levantia | 6 | 4 | 3 | 3 | 0 |
| Formosa | 4 | 3 | 0 | 2 | 0 |
| Phrygia | 6 | 3 | 0 | 1 | 1 |
| Yamato | 3 | 3 | 0 | 2 | 2 |
| Solaria | 3 | 3 | 0 | 1 | 0 |
| Choson | 8 | 1 | 2 | 1 | 0 |
| Hanguk | 5 | 3 | 0 | 2 | 1 |
| Caribe | 3 | 0 | 0 | 0 | 0 |
| Mirage | 2 | 2 | 0 | 1 | 0 |

**Changes from Q1 2026 research baseline to Template v1.0:** see CHANGES_LOG.md "Template v1.0 Force Structure Locked" section for 14-row rationale table.

### 6.2 Real-world basis (Q1 2026 OSINT)

Deployments informed by publicly reported Q1 2026 posture:
- **Russia-Ukraine:** Pokrovsk fall (late Jan), Fortress Belt offensive (Mar 21).
- **US-Iran (Op Epic Fury, 28 Feb):** 3 Carrier Strike Groups in CENTCOM.
- **Israel multi-front ops:** Lebanon (3 divisions), Gaza, Syria buffer.
- **US Caribbean residual** following Maduro capture (3 Jan).
- **Germany 45th Brigade** operational in Lithuania (Feb).
- **THAAD/Patriot layered** across Gulf states.

### 6.2a Starting basing rights (added 2026-04-08)

Reflects real-world military base parallels at game start. Stored in `relationships` table (`basing_rights_a_to_b = true` means from_country hosts to_country's forces).

| Host country | Guest country | Real-world parallel |
|---|---|---|
| Yamato | Columbia | Okinawa, Yokosuka |
| Hanguk | Columbia | Camp Humphreys |
| Teutonia | Columbia | Ramstein, Stuttgart |
| Albion | Columbia | RAF Lakenheath, Menwith Hill |
| Phrygia | Columbia | Incirlik |
| Formosa | Columbia | Informal military presence |
| Mirage | Columbia | Al Dhafra |
| Ponte | Columbia | Aviano, Sigonella |
| Freeland | Columbia | Redzikowo BMD site |
| Choson | Sarmatia | Advisory + logistics presence |
| Sarmatia | Choson | Training + diplomatic presence |
| Mirage | Gallia | Djibouti (Camp Lemonnier parallel) |

**12 basing records total.** Basing rights are tradeable assets during play (grant/revoke via transactions or agreements).

### 6.3 Design principles applied

- **At-war reserves minimized:** at-war countries (Sarmatia, Persia, Ruthenia, Columbia-against-Iran, Levantia) are fully committed, minimal reserve share.
- **Peace-country reserve share ≥ 20%** (Bharata, Cathay strategic buffer).
- **Columbia forward-deployed** with CONUS homeland floor (≥3 CONUS AD after 4→6 bump).
- **Iran dispersal:** Persia ground/air spread across 7 theater hexes, no stacking.
- **No Sarmatian forces on free Ruthenia** (`ruthenia_1`). Only on `ruthenia_2` = contested/occupied zone.
- **No Columbia forces on Persian soil** (`persia_*` / theater persia cells). Near-Persia reach via water (Gulf, Red Sea) and allied basing only.
- **Strategic missiles centrally placed** in owner's interior; forward Iskander deployment only on occupied territory.
- **Die Hard hex hardened** with ground fortress + AD Patriot/NASAMS coverage + close air support.

---

## 7. Changes from pre-Template-v1.0

### 7.1 `zone_id` retired → pure coordinate schema (2026-04-05)

The legacy `zone_id` string field (e.g. `col_main_1`, `ruthenia_2`, `t_persia_17`, `w(13,9)`) has been replaced with explicit `(global_row, global_col, theater, theater_row, theater_col)` coordinate fields on every unit. All zone-lookup tables (`ZONE_TO_HEX`, `MASHRIQ_ZONE_LINKS`, `persiaZoneToGlobal`, etc.) are deleted from the renderer. 344 unit rows migrated, per-country-per-type totals preserved exactly. Legacy CSV kept at `C4_DATA/units_legacy_zone_id.csv`.

### 7.2 Self-occupation bug fixed

Eastern Ereb theater cell at `(theater_row=5, theater_col=8)` previously had `owner=sarmatia, occupied_by=sarmatia`. A country cannot occupy its own territory — `occupied_by` is now cleared. Backup preserved at `SEED_C3_THEATER_EASTERN_EREB_STATE_v3.json.bak_pre_fix`. Full-file scan confirmed this was the only such cell in Eastern Ereb. Mashriq JSON has no `occupied_by` fields set at Template v1.0.

### 7.3 Columbia AD 4 → 6

Increased Columbia air_defense from 4 to 6 units in `countries.csv`. Rationale: previous 4-unit total left zero CONUS homeland AD (all 4 forward-deployed). Now 3 CONUS (GBI Fort Greely + 2 sector) + 3 forward (Europe, Pacific, Gulf). Restores basic homeland missile-defense baseline.

### 7.4 Canonical theater↔global linkage established (v2 final)

The mapping in §1.5 replaces prior ad-hoc mappings in structure docs and code. Key corrections vs prior state:
- **Eastern Ereb sea** now aggregates to `(5, 12)` (was unset / variable).
- **Ruthenia** collapses to one global hex `(4, 11)` regardless of free/occupied status (previously split `(12,4)` vs `(12,5)` under the old 12×N row convention).
- **Sarmatia** split by theater row at 1-4 vs 5+ → `(3,12)` vs `(4,12)`.
- **Persia** split by theater row at 1-3 / 4-6 / 7-10.
- **Mashriq sea** split by theater row at 3-6 vs 7-10.

22 units in `units.csv` had their global coords re-synced to match. 28 units in `start_one.csv` likewise. Theater coords were not modified.

### 7.5 Coordinate convention unified on `(row, col)`

All runtime code, all NEW data files, and all SEED tables now use `(row, col)`. Legacy theater JSON `global_link` string values that still encode `(col, row)` are flipped by the viewer on read; the JSONs themselves are frozen. (Mashriq theater JSON is updated by this exercise to add `global_link` in canonical `(row, col)` form.)

---

## 8. References

### Related SEED docs

- `2 SEED/C_MECHANICS/C1_MAP/SEED_C1_MAP_STRUCTURE_v4.md` — global land-hex registry + chokepoints.
- `2 SEED/C_MECHANICS/C1_MAP/SEED_C3_THEATER_EASTERN_EREB_STRUCTURE_v3.md` — Eastern Ereb land-hex registry.
- `2 SEED/C_MECHANICS/C1_MAP/SEED_C3_THEATER_MASHRIQ_STRUCTURE_v1.md` — Mashriq land-hex registry.
- `2 SEED/D_ENGINES/SEED_D_UNIT_DATA_MODEL_v1.md` — formal unit schema spec.
- `2 SEED/H_VISUAL/SEED_H1_UX_STYLE_v2.md` — map color palette, icon set.

### Data files

- `2 SEED/C_MECHANICS/C1_MAP/SEED_C1_MAP_GLOBAL_STATE_v4.json` — global hex ownership.
- `2 SEED/C_MECHANICS/C1_MAP/SEED_C3_THEATER_EASTERN_EREB_STATE_v3.json` — Eastern Ereb hexes + Die Hard.
- `2 SEED/C_MECHANICS/C1_MAP/SEED_C3_THEATER_MASHRIQ_STATE_v1.json` — Mashriq hexes (now with `global_link`).
- `2 SEED/C_MECHANICS/C4_DATA/units_layouts/start_one.csv` — **CANONICAL Template v1.0 unit placement + force structure (345 units).** Authoritative source.
- `2 SEED/C_MECHANICS/C4_DATA/units.csv` — engine default, identical snapshot of start_one.csv at lock-time.
- `2 SEED/C_MECHANICS/C4_DATA/countries.csv` — per-country force totals (20 countries). **Derived** summary of start_one.csv aggregates.

### Code modules

- `app/engine/agents/map_context.py` — `load_units()`, `units_by_global_hex()`, `units_by_theater_cell()`.
- `app/test-interface/server.py` — `/api/map/*` endpoints.
- `app/test-interface/static/map.js` — renderer, `globalHexForTheaterCell()`, aggregation.
- `app/test-interface/templates/map.html` — viewer shell.

---

*This document is the keystone reference for map + units. When in doubt about linkage, schema, or placement rules, cite this file first.*
