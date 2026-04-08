# DET F — Scenario Configuration Schema

**Version:** 1.0
**Status:** Canonical
**Date:** 2026-04-05
**Owner:** LEAD + BACKEND
**Authoritative source:** `.claude/plans/golden-nibbling-starlight.md` (Marat-approved, 12 decisions locked)

---

## 1. Purpose

This document is the canonical specification of the `sim_templates` / `sim_scenarios` data model and the `run_config` JSONB snapshot carried on `sim_runs`. It closes **Critical Gap 1** identified in `CONCEPT TEST/CHANGES_LOG.md` — "scenario config was architected but never formally specified."

Everything a facilitator can customize for a live TTT event lives in the SCENARIO. Everything that defines the game itself (map, formulas, role library) lives in the TEMPLATE. Everything that describes an actual playthrough lives in the SIM-RUN. This document says, field by field, which layer owns what, and how fields resolve at runtime.

Once merged, this document is the contract that:
- `DET_B1_DATABASE_SCHEMA.sql` implements
- `DET_B1a_TEMPLATE_TAXONOMY.sql` extends
- SEED seed files (template v1.0, scenario start_one) populate
- The engine reads via a single `get_field(scenario, template, path)` resolver
- The facilitator UI (future sprint) exposes as form fields

---

## 2. Design Principle: Sparse Override

**A SCENARIO is a modified copy of TEMPLATE with sparse overrides.**

- Every field a scenario can set has a template-level default (or is explicitly "scenario-owned").
- A scenario stores **only** the fields it wants to change.
- At read time, the engine falls back to template values for unset fields.

**Why sparse?** Scenarios must be small, clear, and auditable. A facilitator should be able to open a scenario record and see "these 6 things differ from Template v1.0" — not re-read the entire game.

**Consequence:** Scenario JSONB columns are **additive diffs**, never full snapshots. Full snapshots only exist on `sim_runs.run_config` (frozen at run start).

**Three ownership buckets (used throughout §5):**
1. **Scenario-OWNED** — no template default exists; scenario must provide (e.g., event venue, facilitator IDs).
2. **Template selections** — template declares an allowed range/set; scenario picks within it (e.g., max rounds, oil price).
3. **Scenario OVERRIDES** — template has a default; scenario may change it (e.g., a specific country's starting GDP).

---

## 3. Three-Level Model

```
┌───────────────────────────────────────────────────────────────────┐
│ TEMPLATE  ("TTT Power Transition 2026 v1.0")                      │
│ - Map topology, theaters, chokepoints                             │
│ - Country master list + canonical starting stats                  │
│ - Role library + default briefings + default personas             │
│ - Formula coefficients (LOCKED — not overridable)                 │
│ - Default relationship matrix                                     │
│ - Default unit deployment layout                                  │
│ - Allowed ranges: round count, oil price, theater set             │
│ - Semver: 1.0, 1.1, 2.0 … multiple coexist in DB                  │
└───────────────────────────────────────────────────────────────────┘
                              │  FK: scenario.template_id
                              ▼
┌───────────────────────────────────────────────────────────────────┐
│ SCENARIO  ("Davos 2026 TTT — April cohort")                       │
│ - Event metadata: venue, facilitators, participants, date         │
│ - SIM starting date (in-fiction, e.g., "Q1 2026")                 │
│ - Max rounds chosen (∈ template.allowed_round_counts)             │
│ - Oil price starting value (∈ template.allowed_oil_price_range)   │
│ - Theater activation (⊆ template.allowed_theaters)                │
│ - Role assignments (⊆ template roles + user bindings placeholder) │
│ - Election schedule, scripted event timeline                      │
│ - Sparse overrides (JSONB diffs):                                 │
│     country_stat_overrides, relationship_overrides,               │
│     role_briefing_overrides, role_persona_overrides,              │
│     unit_layout_id (FK or NULL = use template default)            │
└───────────────────────────────────────────────────────────────────┘
                              │  FK: sim_run.scenario_id
                              ▼
┌───────────────────────────────────────────────────────────────────┐
│ SIM-RUN  (one playthrough, immutable once started)                │
│ - run_config: frozen scenario snapshot (merged with template)     │
│ - User ↔ role bindings                                            │
│ - Per-round world_state + country_state snapshots                 │
│ - Append-only event log (behavioral truth)                        │
│ - Per-role, per-run agent memories                                │
└───────────────────────────────────────────────────────────────────┘
```

**Hard-coded (per Q-A, NOT in any data layer):** action catalog, event-type taxonomy, engine implementations, 4-block cognitive architecture, round phase structure (A/B/C), Realtime channels, UI layouts.

---

## 4. TEMPLATE Schema (fields owned by template)

Templates evolve on semver (`1.0` → `1.1` patch, `2.0` major). Multiple templates coexist; scenarios reference a specific `template_id`. A template is **immutable once published** — edits bump the version.

| Field | Type | Description | Example | Overridable by scenario? |
|---|---|---|---|---|
| `id` | UUID | PK | — | — |
| `code` | TEXT | Short machine code | `ttt_power_transition` | — |
| `name` | TEXT | Human name | `TTT Power Transition 2026` | — |
| `version` | TEXT | Semver | `1.0` | — |
| `description` | TEXT | Editor summary | `First locked build, Q1 2026` | — |
| `status` | ENUM | `draft \| published \| deprecated` | `published` | — |
| `created_at` | TIMESTAMPTZ | | | — |
| **Map topology** | | | | |
| `map_topology` | JSONB / linked rows | Hexes, adjacency, theaters, chokepoints, zone owners | see `map_config.py` | **No** |
| `allowed_theaters` | TEXT[] | Theaters that can be activated | `[eastern_ereb, mashriq, taiwan_strait, indo_pacific]` | Selection only |
| **Countries** | | | | |
| `countries` | linked table rows | Master list + stats (GDP, inflation, treasury, military, tech, stability) | see `countries.csv` | Yes (overrides) |
| **Roles** | | | | |
| `roles` | linked table rows | Role library + default briefings + default personas | see SEED A1 | Yes (overrides) |
| **Relationships** | | | | |
| `default_relationships` | linked table rows | Bilateral tension / alliance / tariff / sanction matrix | | Yes (overrides) |
| **Units** | | | | |
| `default_unit_layout_id` | UUID FK | Default deployment layout (`units.csv`) | 345 units | Yes (swap layout) |
| **Formulas (LOCKED per Q3)** | | | | |
| `formula_coefficients` | JSONB | All engine coefficients (GDP, oil, sanctions, combat, …) | see `DET_A2` | **NO — template-locked** |
| **Allowed ranges (scenario picks within)** | | | | |
| `allowed_round_counts` | INT[] | Valid max_round choices | `[6, 8]` | Selection only |
| `allowed_oil_price_range` | NUMERIC[2] | `[min, max]` | `[50, 150]` | Selection only |
| `allowed_phase_a_duration_range` | INT[2] | `[min, max]` seconds | `[300, 1200]` | Selection only |
| **Hard-coding references** | | | | |
| `engine_version_required` | TEXT | Minimum code version compatible | `0.4.x` | — |
| `action_catalog_version` | TEXT | Referenced, not stored | `v1.0` | — |

> **Storage note:** `allowed_oil_price_range` and `allowed_phase_a_duration_range` are stored in PostgreSQL as `NUMRANGE` and `INT4RANGE` respectively (see `DET_B1a_TEMPLATE_TAXONOMY.sql`). The table above shows them as `NUMERIC[2]` / `INT[2]` for logical clarity. The scenario resolver uses `lower(range)` and `upper(range)` for bounds checking.

See `DET_B1a_TEMPLATE_TAXONOMY.sql` (sibling doc) for the literal DDL.

---

## 5. SCENARIO Schema (complete field list)

A scenario has **four logical blocks**: identity, scenario-owned fields, template selections, and sparse overrides. In DB they flatten onto one `sim_scenarios` row with JSONB columns for the override blocks.

### 5.1 Identity

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | UUID | yes | PK |
| `template_id` | UUID FK | yes | References `sim_templates(id)` |
| `code` | TEXT | yes | Short machine code, unique per template |
| `name` | TEXT | yes | Human label |
| `status` | ENUM | yes | `draft \| ready \| archived` |
| `created_at` | TIMESTAMPTZ | yes | — |
| `updated_at` | TIMESTAMPTZ | yes | — |

### 5.2 Scenario-OWNED fields (no template default)

Stored as a single JSONB column `scenario_owned` (preferred) OR as first-class columns (implementation choice; BACKEND agent decides, but shape is canonical).

| JSON path | Type | Required | Validation | Example |
|---|---|---|---|---|
| `event.venue` | string | yes | ≤ 200 chars | `"Davos Congress Centre"` |
| `event.event_name` | string | yes | ≤ 200 chars | `"WEF TTT 2026"` |
| `event.event_date` | ISO date | yes | future-ish | `"2026-04-15"` |
| `event.facilitator_ids` | UUID[] | yes | min 1 | `["uuid-…"]` |
| `event.participant_count` | int | yes | 0..100 | `32` |
| `event.participant_profile` | string | no | free text ≤ 500 | `"C-level, mixed industries"` |
| `event.delivery_format` | enum | yes | `in_person \| hybrid \| remote` | `"in_person"` |
| `event.learning_objectives` | string[] | no | ≤ 10 items | `["Understand Thucydides Trap"]` |
| `sim.starting_date_in_fiction` | string | yes | free text | `"Q1 2026"` |

### 5.3 Template selections (within template-allowed ranges)

These are **required choices** from template-declared ranges. Stored as first-class columns on `sim_scenarios` for easy indexing.

| Column | Type | Required | Validation | Example |
|---|---|---|---|---|
| `max_rounds` | INT | yes | `∈ template.allowed_round_counts` | `8` |
| `oil_price_start` | NUMERIC | yes | `∈ template.allowed_oil_price_range` | `78.5` |
| `phase_a_duration_seconds` | INT | yes | `∈ template.allowed_phase_a_duration_range` | `600` |
| `active_theaters` | TEXT[] | yes | `⊆ template.allowed_theaters` | `["eastern_ereb","taiwan_strait"]` |

### 5.4 Scenario OVERRIDES (sparse, optional)

Each block is a JSONB column on `sim_scenarios`. All are optional. Unset keys fall back to template.

| Column | JSON shape (summary) | Default behavior |
|---|---|---|
| `country_stat_overrides` | `{<country_code>: {<stat>: <value>}}` | Fall back to template country row |
| `relationship_overrides` | `{<from_code>__<to_code>: {tension, alliance, tariff_pct, sanction_tier}}` | Fall back to template bilateral row |
| `role_briefing_overrides` | `{<role_code>: {briefing_addendum?, briefing_replace?}}` | Fall back to template briefing |
| `role_persona_overrides` | `{<role_code>: {persona_addendum?, persona_replace?}}` | Fall back to template persona |
| `unit_layout_id` | UUID FK nullable | `NULL` → use `template.default_unit_layout_id` |
| `scripted_events` | `[{round, phase, event_type, payload}]` | Empty = no scripted events |
| `election_schedule` | `{<country_code>: {election_type, round}}` | Empty = no elections during SIM |
| `role_assignments` | `[{role_code, active: bool, binding?: "human"\|"ai"}]` | Missing = role inactive OR template default |

Concrete JSON shapes in §10.

---

## 6. Organizations

Organizations (UNSC, Ereb Union, OPEC, BRICS, NATO, G7, EU, Parliament, etc.) are a **distinct entity type** — they are NOT countries.

**Core distinctions:**
- Organizations do **NOT** own assets (no treasury of their own by default, no GDP).
- Organizations do **NOT** move troops.
- Organizations **DO** have: memberships, meetings, collective decisions.
- **Collective decisions are NOT automatically executed.** Every org output is a recommendation/declaration. Member countries may or may not follow it. The engine does not force compliance; it logs the declaration and the subsequent member behavior separately.

This closes **Gap 2 (Organization Mechanics Underspecified)** at the taxonomy level. Detailed voting mechanics are deferred to `SEED_C8_ORGANIZATIONS_v1.md` (future sprint).

### 6.1 Template-owned (canonical defaults, frozen per version)

Stored in a template-level organizations catalog:

| Field | Type | Description |
|---|---|---|
| `code` | TEXT | Machine code (e.g., `un_security_council`, `ereb_union`, `opec`, `brics`, `nato`, `g7`, `eu_council`, `parliament`) |
| `name` | TEXT | Human name |
| `description` | TEXT | Mandate + scope narrative |
| `scope` | ENUM | `global \| regional \| sectoral` |
| `eligibility_rules` | JSONB | Who CAN join (e.g., regional filter, treaty prerequisites) |
| `meeting_mechanics` | JSONB | Who can call a meeting, default frequency, format (summit / session / emergency) |
| `decision_mechanics` | JSONB | Voting rule: `consensus \| simple_majority \| supermajority \| veto_enabled` (plus veto holder list where relevant) |
| `enforcement_status` | ENUM | **Always `none`** for v1.0 — all decisions are recommendations/declarations, non-binding on members |
| `default_memberships` | TEXT[] | Country codes that start in the org |

### 6.2 Scenario-level customization (sparse overrides)

- **`active_organizations`** (TEXT[]) — subset of `template.organizations[*].code` enabled for this scenario. Empty → none active.
- **`organization_overrides`** (JSONB) — sparse membership diffs:

```json
{
  "<org_code>": {
    "add_members": ["TEU"],
    "remove_members": ["RUS"]
  }
}
```

  Example: `{ "ereb_union": { "remove_members": ["TEU"] } }` models "Teutonia has left Ereb Union in this scenario."

- **Scheduled org meetings** — fit under §5.4 `scripted_events` with `event_type: "org_meeting_scheduled"`:

```json
{
  "round": 2,
  "phase": "A",
  "event_type": "org_meeting_scheduled",
  "payload": {
    "org_code": "un_security_council",
    "agenda": "response to Taiwan Strait incident",
    "mandatory": true
  }
}
```

### 6.3 SIM-RUN state (dynamic, not in scenario config)

Organizations produce dynamic state during a run, captured in existing SIM-RUN tables:

- **Current memberships** — `org_memberships` table (already exists in DET_B1). Can mutate during play via `join_org` / `leave_org` actions.
- **Meeting history** — each meeting is a row in the event log (`event_type: org.meeting_called`).
- **Decision records** — vote tally per meeting: `event_type: org.decision_voted`, payload includes per-member `supported | opposed | abstained`.
- **Declaration log** — each declaration is logged separately: `event_type: org.declaration_issued`. The engine does NOT auto-apply the declaration; subsequent member actions are tracked independently so the report can show declaration vs compliance.

### 6.4 JSONB structures to spec

Summary of new shapes introduced by this section:

- **`template.organizations`** — full catalog (see §6.1 table).
- **`scenario.organization_overrides`** — sparse membership diffs (see §6.2).
- **`scenario.active_organizations`** — activation list.
- **`scripted_events[*].event_type = "org_meeting_scheduled"`** — extends the scripted-events taxonomy.
- **Run event types (code-backed, added to event-type taxonomy):**
  - `org.meeting_called`
  - `org.decision_voted`
  - `org.declaration_issued`

**Out of scope for DET F v1.0 (deferred to `SEED_C8_ORGANIZATIONS_v1.md`):** detailed voting rule formalization, veto interaction with abstention, weighted voting, quorum rules, meeting agenda generation, declaration templating.

---

## 7. SIM-RUN Schema (`run_config` JSONB)

A SIM-RUN is created from a scenario by **freezing a full snapshot**. `sim_runs.run_config` contains the merged template+scenario state at the moment the run started. After that moment, scenario edits do NOT affect the live run.

`run_config` shape:

```json
{
  "template_id": "uuid-…",
  "template_version": "1.0",
  "scenario_id": "uuid-…",
  "scenario_code": "davos_2026_april",
  "frozen_at": "2026-04-15T09:00:00Z",
  "resolved": {
    "max_rounds": 8,
    "oil_price_start": 78.5,
    "phase_a_duration_seconds": 600,
    "active_theaters": ["eastern_ereb","taiwan_strait"],
    "countries": { "<code>": { /* full merged stats */ } },
    "relationships": [ /* full merged matrix */ ],
    "roles": [ /* full merged role list with briefing + persona */ ],
    "formula_coefficients": { /* copied verbatim from template */ },
    "unit_layout_id": "uuid-…",
    "scripted_events": [ ... ],
    "election_schedule": { ... },
    "role_assignments": [ ... ]
  }
}
```

**Invariant:** `run_config` is written once at status `setup → active` and never mutated after.

**Rationale:** If a template is bumped to v1.1 mid-event, running SIMs must remain reproducible against v1.0. The snapshot guarantees this.

---

## 8. Validation Rules

### 8.1 Hard constraints (enforced at DB + API layer)

- **FK integrity:** `scenario.template_id` exists; `scenario.unit_layout_id` (if set) exists; all country codes in overrides exist in the template's country list; all role codes exist.
- **Enums:** `status`, `delivery_format`, country stat keys, relationship keys.
- **Range selections:**
  - `max_rounds ∈ template.allowed_round_counts`
  - `oil_price_start ∈ [allowed_oil_price_range.min, allowed_oil_price_range.max]`
  - `phase_a_duration_seconds ∈ [lower(allowed_phase_a_duration_range), upper(allowed_phase_a_duration_range)]`
  - `active_theaters ⊆ template.allowed_theaters` and non-empty.
- **Event fields:** `facilitator_ids` non-empty; `participant_count ≥ 0`; `event_date` is a valid ISO date.
- **Scripted events:** each `round ∈ [1, max_rounds]`; each `event_type` must be a code-recognized event type (validated against the hard-coded taxonomy at scenario-save time).
- **Election schedule:** each round ∈ `[1, max_rounds]`; each `election_type` is a known enum (`presidential`, `parliamentary`, `leadership_review`).
- **Override stat values:** country stat overrides use only keys that exist on the template country row; values within plausible numeric ranges (e.g., GDP > 0).

### 8.2 Soft warnings (editor-level, non-blocking)

- Country stat override deviates >50% from template value → warn "large deviation — formula calibration may not hold."
- Relationship override flips alliance sign → warn "reversing polarity of a calibrated relationship."
- Theater activation excludes all template theaters containing chokepoints → warn "no chokepoint theaters active; combat engine reach limited."
- Max rounds at lower bound combined with many scripted events → warn "event density may exceed playable pace."
- Role briefing replacement >10× template length → warn "prompt budget risk."

### 8.3 Template-LOCKED fields (CANNOT be overridden at scenario level)

Per Q3 + Q-A:

- **Formula coefficients** (all engines: GDP, oil, sanctions, combat, tech, stability, …). Locked to preserve calibration.
- **Map topology** (hexes, adjacency, zones, theaters, chokepoints).
- **Action catalog** (code-backed).
- **Event-type taxonomy** (code-backed).
- **Engine implementations** (code-backed).
- **Cognitive architecture** (4-block model, code-backed).
- **Round phase structure** (A/B/C, code-backed).

Attempting to set any of these on a scenario is a **hard validation error**.

---

## 9. Resolution Algorithm (runtime field access)

Every engine read goes through a single resolver:

```python
def get_field(scenario, template, field_path):
    """
    Resolve a field for a scenario, falling back to template.
    Precedence: scenario overrides > scenario owned/selections > template default.
    """
    # 1. Scenario sparse overrides (e.g., country.CHN.gdp)
    if field_path in scenario.overrides_index:
        return scenario.overrides_index[field_path]

    # 2. Scenario-owned fields or template selections
    if field_path in scenario.owned_index:
        return scenario.owned_index[field_path]

    # 3. Fall back to template default
    if field_path in template.index:
        return template.index[field_path]

    raise KeyError(f"Field {field_path} not found in scenario, template, or code.")
```

**At run start**, the resolver is invoked for every field to produce `run_config.resolved`. After that, engines read from `run_config.resolved` directly (no further resolution needed mid-run).

**Field paths use dot notation**, e.g.:
- `country.CHN.gdp`
- `relationship.USA__CHN.tension`
- `role.usa_president.briefing`
- `sim.max_rounds`
- `sim.oil_price_start`

---

## 10. Examples

### 10.1 Minimal scenario (no overrides)

A scenario that takes template defaults for everything except event metadata and required selections:

```json
{
  "id": "sce-0001",
  "template_id": "tpl-v1-0",
  "code": "smoke_test_001",
  "name": "Smoke Test 001",
  "status": "ready",
  "max_rounds": 8,
  "oil_price_start": 78.0,
  "phase_a_duration_seconds": 600,
  "active_theaters": ["eastern_ereb","taiwan_strait","mashriq","indo_pacific"],
  "scenario_owned": {
    "event": {
      "venue": "Internal Lab",
      "event_name": "Smoke Test 001",
      "event_date": "2026-04-10",
      "facilitator_ids": ["usr-marat"],
      "participant_count": 0,
      "delivery_format": "remote"
    },
    "sim": { "starting_date_in_fiction": "Q1 2026" }
  },
  "country_stat_overrides": {},
  "relationship_overrides": {},
  "role_briefing_overrides": {},
  "role_persona_overrides": {},
  "unit_layout_id": null,
  "scripted_events": [],
  "election_schedule": {},
  "role_assignments": []
}
```

### 10.2 Scenario with `country_stat_overrides`

"What if China's GDP started 15% higher and Russia's stability was lower?"

```json
{
  "country_stat_overrides": {
    "CHN": { "gdp": 21500, "treasury": 3400 },
    "RUS": { "stability": 42 }
  }
}
```

### 10.3 Scenario with scripted event timeline

```json
{
  "scripted_events": [
    { "round": 1, "phase": "A", "event_type": "org_meeting_mandatory",
      "payload": { "org_code": "un_security_council", "agenda": "opening session" } },
    { "round": 3, "phase": "B", "event_type": "oil_shock",
      "payload": { "delta_usd_per_barrel": 25, "reason": "Strait of Hormuz disruption" } },
    { "round": 5, "phase": "A", "event_type": "election",
      "payload": { "country": "USA", "election_type": "presidential" } }
  ]
}
```

### 10.4 Scenario with role assignments

```json
{
  "role_assignments": [
    { "role_code": "usa_president",     "active": true, "binding": "human" },
    { "role_code": "usa_sec_state",     "active": true, "binding": "human" },
    { "role_code": "chn_president",     "active": true, "binding": "human" },
    { "role_code": "rus_president",     "active": true, "binding": "ai" },
    { "role_code": "irn_supreme_leader","active": true, "binding": "ai" },
    { "role_code": "prk_leader",        "active": false }
  ]
}
```

User ↔ role bindings (`user_id` per role) happen at SIM-RUN creation, not on the scenario.

---

## 11. JSONB Structure Specifications

### 11.1 `scenario_owned`

```json
{
  "event": {
    "venue": "string",
    "event_name": "string",
    "event_date": "YYYY-MM-DD",
    "facilitator_ids": ["uuid", "..."],
    "participant_count": 0,
    "participant_profile": "string?",
    "delivery_format": "in_person|hybrid|remote",
    "learning_objectives": ["string", "..."]
  },
  "sim": {
    "starting_date_in_fiction": "string"
  }
}
```

### 11.2 `country_stat_overrides`

```json
{
  "<country_code>": {
    "gdp": "number?",
    "gdp_growth_pct": "number?",
    "inflation_pct": "number?",
    "treasury": "number?",
    "military_strength": "number?",
    "tech_level": "number?",
    "stability": "number?"
  }
}
```

Any subset of stats may be overridden per country.

### 11.3 `relationship_overrides`

```json
{
  "<from_code>__<to_code>": {
    "tension": "number?",
    "alliance_level": "number?",
    "tariff_pct": "number?",
    "sanction_tier": "0|1|2|3?"
  }
}
```

Key format: `<A>__<B>` (double underscore) to denote directed pair A → B.

### 11.4 `role_briefing_overrides`

```json
{
  "<role_code>": {
    "briefing_addendum": "string?",
    "briefing_replace": "string?"
  }
}
```

If both keys present, `briefing_replace` wins. `addendum` is appended after template briefing with a `\n\n---\n` separator.

### 11.5 `role_persona_overrides`

```json
{
  "<role_code>": {
    "persona_addendum": "string?",
    "persona_replace": "string?",
    "trait_deltas": { "<trait>": "number?" }
  }
}
```

`trait_deltas` shifts template trait scores (e.g., `aggression: +10`). Applied only if neither `persona_replace` nor `persona_addendum` is given, OR stacks additively with `addendum`.

### 11.6 `scripted_events`

```json
[
  {
    "round": 1,
    "phase": "A|B|C",
    "event_type": "string (code-validated)",
    "payload": { "... event-type-specific ..." },
    "mandatory": true
  }
]
```

`event_type` must match an entry in the code-side event-type taxonomy.

### 11.7 `election_schedule`

```json
{
  "<country_code>": {
    "election_type": "presidential|parliamentary|leadership_review",
    "round": 5
  }
}
```

### 11.8 `role_assignments`

```json
[
  {
    "role_code": "string",
    "active": true,
    "binding": "human|ai"
  }
]
```

`binding` is a **default hint**. Actual user↔role binding happens at `sim_runs` creation.

### 11.9 `run_config.resolved` (SIM-RUN snapshot)

See §7. Structurally the union of all resolved template + scenario fields; no sparse semantics (every field populated).

---

## 12. Template Allowed-Ranges Specification

Templates declare what scenarios may customize via a dedicated `allowed_ranges` JSONB (or first-class columns). Canonical shape:

```json
{
  "allowed_round_counts": [6, 8],
  "allowed_oil_price_range": [50, 150],
  "allowed_phase_a_duration_range": [300, 1200],
  "allowed_theaters": [
    "eastern_ereb",
    "mashriq",
    "taiwan_strait",
    "indo_pacific",
    "arctic"
  ],
  "allowed_scripted_event_types": [
    "org_meeting_mandatory",
    "oil_shock",
    "election",
    "natural_disaster",
    "tech_breakthrough",
    "leadership_change"
  ],
  "allowed_election_types": [
    "presidential",
    "parliamentary",
    "leadership_review"
  ],
  "override_policy": {
    "country_stats": "free",
    "relationships": "free",
    "role_briefings": "free",
    "role_personas": "free",
    "formula_coefficients": "locked",
    "map_topology": "locked",
    "action_catalog": "locked"
  }
}
```

A future template could narrow these (e.g., publish a "Training" template with `allowed_round_counts: [4]` only).

---

## 13. Open Questions / Future Expansion

Deferred to later sprints — flagged here so no one silently invents:

- **Detailed organization voting mechanics** — quorum rules, weighted voting, veto-abstention interactions. Deferred to `SEED_C8_ORGANIZATIONS_v1.md`.
- **Covert operations customization** — template-level covert action catalog + scenario-level enablement. Waiting on covert-ops DET.
- **Intra-round time controls** — per-phase timers, pause/resume config. Current: scenario sets `phase_a_duration_seconds` only.
- **Facilitator overrides mid-run** — scenario-level allow-list for mid-run interventions (injected events, parameter nudges). Separate gap.
- **Multi-template crossovers** — e.g., a scenario referencing roles from two templates. Explicitly OUT of scope for v1.0.
- **Scenario inheritance / templates-of-templates** — child scenarios inheriting from parent scenarios. OUT of scope; use template semver instead.
- **Localization / multi-language briefings** — future; no current field.
- **Observability of override audit trail** — currently inferred from `scenario.updated_at`; no per-field history yet.

---

## 14. References

- **Canonical plan (source of truth for 12 decisions):** `.claude/plans/golden-nibbling-starlight.md`
- **Master SEED (map + units):** `2 SEED/C_MECHANICS/SEED_C_MAP_UNITS_MASTER_v1.md`
- **Existing DB schema:** `3 DETAILED DESIGN/DET_B1_DATABASE_SCHEMA.sql` (v1.2, 2026-04-03)
- **Template taxonomy SQL (sibling doc):** `3 DETAILED DESIGN/DET_B1a_TEMPLATE_TAXONOMY.sql`
- **Template v1.0 seed:** `CONCEPT TEST/template_v1_0_seed.sql`
- **Scenario start_one seed:** `CONCEPT TEST/scenario_start_one_seed.sql`
- **Changes log:** `CONCEPT TEST/CHANGES_LOG.md`
- **Role calibration (briefings/personas):** `3 DETAILED DESIGN/DET_A1_ROLE_CALIBRATION_v1.md`
- **Formula coefficients (LOCKED):** `3 DETAILED DESIGN/DET_A2_DATA_CALIBRATION.md`
- **Engine API:** `3 DETAILED DESIGN/DET_F5_ENGINE_API.md`
- **Naming conventions:** `3 DETAILED DESIGN/DET_NAMING_CONVENTIONS.md`
- **Organizations (future):** `2 SEED/C_MECHANICS/SEED_C8_ORGANIZATIONS_v1.md` (detailed voting mechanics — future sprint)

---

*End of DET F v1.0.*
