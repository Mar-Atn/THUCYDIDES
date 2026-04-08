-- =====================================================================
-- TTT — Template / Scenario / Run Taxonomy (schema additions)
-- File: DET_B1a_TEMPLATE_TAXONOMY.sql
-- Target: PostgreSQL 15+ / Supabase
-- Version: 1.0 (draft, 2026-04-05)
-- Author: Build team (under Marat's 12 locked decisions)
-- Companion doc: DET_F_SCENARIO_CONFIG_SCHEMA.md (canonical spec)
-- Companion seed: CONCEPT TEST/template_v1_0_seed.sql,
--                 CONCEPT TEST/scenario_start_one_seed.sql
--
-- Scope: formalizes the 3-level TEMPLATE / SCENARIO / SIM-RUN model.
-- Does NOT modify the existing DET_B1_DATABASE_SCHEMA.sql — instead
-- adds taxonomy tables that the main schema can be reconciled against
-- in a follow-up integration pass.
--
-- Core principle (Marat, 2026-04-05):
--   "A SCENARIO is a sparse override of a TEMPLATE. Every scenario
--    field defaults to its template value; scenario stores only
--    modifications."
-- =====================================================================

-- ---------------------------------------------------------------------
-- Extensions
-- ---------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS "pgcrypto";   -- for gen_random_uuid()

-- =====================================================================
-- 1. TEMPLATES
-- =====================================================================
-- A TEMPLATE is the master SIM definition. It evolves over months,
-- is semver-tracked, and multiple templates can coexist in the DB so
-- older scenarios keep their frozen design.
--
-- Template-owned fields listed below are CANONICAL DEFAULTS — frozen
-- for a given template version. Scenarios may override SOME of them
-- (sparse overrides, per Marat Q1/Q2/Q4/Q5/Q10). Scenarios may NOT
-- override formula_coefficients (Q3: template-locked, preserves
-- calibration).
-- ---------------------------------------------------------------------

CREATE TABLE sim_templates (
    id                         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code                       TEXT UNIQUE NOT NULL,         -- e.g. 'ttt_v1_0'
    name                       TEXT NOT NULL,                -- e.g. 'TTT Power Transition 2026'
    version                    TEXT NOT NULL,                -- semver, e.g. '1.0'
    description                TEXT,
    status                     TEXT NOT NULL DEFAULT 'draft'
                                    CHECK (status IN ('draft','published','deprecated')),

    -- Template-OWNED config (canonical defaults; frozen per version)
    map_config                 JSONB NOT NULL,               -- map dims, theaters, linkage rules
    default_country_stats      JSONB NOT NULL,               -- per-country starting stats (from countries.csv)
    default_relationships      JSONB NOT NULL,               -- bilateral relationship matrix
    default_unit_layout_id     UUID,                         -- FK to unit_layouts (set after layout insert)
    default_role_briefings     JSONB,                        -- per-role briefings + personas
    formula_coefficients       JSONB NOT NULL,               -- LOCKED; scenarios CANNOT override (Q3)
    organizations              JSONB,                        -- catalog of known orgs (UNSC, OPEC, NATO, etc.)

    -- Allowed-range envelopes (what scenarios CAN customize, within bounds)
    allowed_round_counts              INT[]      NOT NULL,   -- e.g. {6, 8}
    allowed_oil_price_range           NUMRANGE   NOT NULL,   -- e.g. '[50.0,150.0]'
    allowed_phase_a_duration_range    INT4RANGE  NOT NULL,   -- seconds, e.g. '[300,1200]'
    allowed_theaters                  TEXT[]     NOT NULL,   -- e.g. {'eastern_ereb','mashriq'}

    created_at                 TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by                 TEXT,

    CHECK (array_length(allowed_round_counts, 1) >= 1),
    CHECK (array_length(allowed_theaters, 1) >= 1)
);

COMMENT ON TABLE  sim_templates IS
    'Master SIM designs. Semver-tracked; multiple coexist. Owns map, default country stats, relationships, unit layout, role briefings, and (LOCKED) formula coefficients.';
COMMENT ON COLUMN sim_templates.code IS
    'Natural key, lowercase/snake_case, e.g. ''ttt_v1_0''.';
COMMENT ON COLUMN sim_templates.formula_coefficients IS
    'FROZEN per template version. Scenarios may not override (preserves calibration).';
COMMENT ON COLUMN sim_templates.allowed_round_counts IS
    'Scenario.max_rounds MUST be an element of this array.';
COMMENT ON COLUMN sim_templates.allowed_oil_price_range IS
    'Scenario.oil_price_start MUST be contained within this range (NUMRANGE; resolver uses lower()/upper()).';
COMMENT ON COLUMN sim_templates.allowed_phase_a_duration_range IS
    'Scenario.phase_a_duration_seconds MUST be contained within this INT4RANGE (e.g. [300,1200]); resolver uses lower()/upper() for bounds checking.';
COMMENT ON COLUMN sim_templates.organizations IS
    'Catalog of known organizations (UNSC, OPEC, NATO, etc.). Scenarios select actives via sim_scenarios.active_organizations.';
COMMENT ON COLUMN sim_templates.allowed_theaters IS
    'Scenario.active_theaters MUST be a subset of this array.';
COMMENT ON COLUMN sim_templates.default_unit_layout_id IS
    'FK to unit_layouts.id for the template''s canonical default deployment.';

CREATE INDEX idx_sim_templates_code    ON sim_templates (code);
CREATE INDEX idx_sim_templates_status  ON sim_templates (status);

-- =====================================================================
-- 2. UNIT LAYOUTS
-- =====================================================================
-- Named deployment snapshots. Each layout belongs to a specific template
-- (so unit_codes resolve against that template's country list) and
-- holds 200-500 rows in layout_units. A template has ONE default
-- layout; scenarios may reference EITHER the template default OR a
-- variant layout.
-- ---------------------------------------------------------------------

CREATE TABLE unit_layouts (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code          TEXT UNIQUE NOT NULL,      -- e.g. 'template_v1_0_default', 'start_one'
    name          TEXT NOT NULL,
    template_id   UUID REFERENCES sim_templates(id) ON DELETE RESTRICT,
    description   TEXT,
    unit_count    INT,                       -- cached row count for convenience
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by    TEXT
);

COMMENT ON TABLE  unit_layouts IS
    'Named unit deployment snapshots. A template has one default layout; scenarios may override via unit_layout_id.';
COMMENT ON COLUMN unit_layouts.template_id IS
    'Which template this layout targets (its country list and unit_codes must match).';
COMMENT ON COLUMN unit_layouts.unit_count IS
    'Denormalized count of layout_units rows; must match actual row count.';

CREATE INDEX idx_unit_layouts_template ON unit_layouts (template_id);

-- FK from sim_templates back to unit_layouts (deferred add — circular ref)
ALTER TABLE sim_templates
    ADD CONSTRAINT fk_sim_templates_default_layout
    FOREIGN KEY (default_unit_layout_id)
    REFERENCES unit_layouts(id)
    ON DELETE SET NULL;

-- ---------------------------------------------------------------------
-- layout_units: the 345 (or N) unit rows belonging to a layout
-- ---------------------------------------------------------------------

CREATE TABLE layout_units (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    layout_id       UUID NOT NULL REFERENCES unit_layouts(id) ON DELETE CASCADE,
    unit_code       TEXT NOT NULL,
    country_code    TEXT NOT NULL,
    unit_type       TEXT NOT NULL
                         CHECK (unit_type IN (
                             'ground','tactical_air','strategic_missile',
                             'air_defense','naval'
                         )),
    global_row      INT CHECK (global_row IS NULL OR global_row BETWEEN 1 AND 10),
    global_col      INT CHECK (global_col IS NULL OR global_col BETWEEN 1 AND 20),
    theater         TEXT,                   -- theater code or NULL
    theater_row     INT CHECK (theater_row IS NULL OR theater_row BETWEEN 1 AND 10),
    theater_col     INT CHECK (theater_col IS NULL OR theater_col BETWEEN 1 AND 10),
    embarked_on     TEXT,                   -- unit_code reference within same layout
    status          TEXT NOT NULL
                         CHECK (status IN ('active','reserve','embarked','destroyed')),
    notes           TEXT,

    UNIQUE (layout_id, unit_code),

    -- theater fields all-or-nothing
    CHECK (
        (theater IS NULL AND theater_row IS NULL AND theater_col IS NULL)
        OR
        (theater IS NOT NULL AND theater_row IS NOT NULL AND theater_col IS NOT NULL)
    ),
    -- active ⇒ global coords set
    CHECK (
        (status <> 'active')
        OR
        (status = 'active' AND global_row IS NOT NULL AND global_col IS NOT NULL)
    ),
    -- embarked ⇒ carrier unit_code set
    CHECK (
        (status <> 'embarked')
        OR
        (status = 'embarked' AND embarked_on IS NOT NULL)
    )
);

COMMENT ON TABLE  layout_units IS
    'Units belonging to a named layout. References carrier units by unit_code (natural key) to enable CSV round-tripping.';
COMMENT ON COLUMN layout_units.embarked_on IS
    'unit_code of carrier within same layout (not a UUID FK). Validated at import time.';

CREATE INDEX idx_layout_units_layout_country ON layout_units (layout_id, country_code);
CREATE INDEX idx_layout_units_layout_status  ON layout_units (layout_id, status);
CREATE INDEX idx_layout_units_global         ON layout_units (global_row, global_col)
    WHERE global_row IS NOT NULL;
CREATE INDEX idx_layout_units_theater        ON layout_units (theater, theater_row, theater_col)
    WHERE theater IS NOT NULL;

-- =====================================================================
-- 3. SCENARIOS
-- =====================================================================
-- A SCENARIO is a sparse override of a template, configured for a
-- specific event (workshop, corporate training, academic session).
--
-- Scenario-OWNED fields have NO template default (event_metadata,
-- sim_starting_date, max_rounds, etc.) — they must always be set.
--
-- Scenario OVERRIDE fields are sparse JSONB — NULL means "use template
-- default for every key"; non-NULL merges over template values key
-- by key.
-- ---------------------------------------------------------------------

CREATE TABLE sim_scenarios (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id                 UUID NOT NULL REFERENCES sim_templates(id) ON DELETE RESTRICT,
    code                        TEXT UNIQUE NOT NULL,       -- e.g. 'start_one', 'davos_2026'
    name                        TEXT NOT NULL,

    -- Scenario-OWNED fields (no template default)
    event_metadata              JSONB NOT NULL,             -- venue, facilitator, participant count, format, objectives
    sim_starting_date           DATE NOT NULL,              -- in-fiction date, e.g. '2026-01-01'
    max_rounds                  INT  NOT NULL,              -- MUST ∈ template.allowed_round_counts
    oil_price_start             NUMERIC(10,2) NOT NULL,     -- MUST ∈ template.allowed_oil_price_range
    phase_a_duration_seconds    INT,                        -- NULL = use template default; DET_F range [300, 1200]
    active_theaters             TEXT[] NOT NULL,            -- MUST ⊆ template.allowed_theaters
    active_organizations        TEXT[],                     -- subset of template.organizations[].code; NULL = none
    election_schedule           JSONB,                      -- [{type, round}, ...]
    scripted_events             JSONB,                      -- [{round, type, payload}, ...]
    role_assignments            JSONB,                      -- DET_F §11.8: [{role_code, active, binding}] where binding is a default hint only
    unit_layout_id              UUID REFERENCES unit_layouts(id) ON DELETE RESTRICT,
                                                            -- NULL = use template default

    -- Scenario OVERRIDES (sparse; NULL means "use template for all keys")
    country_stat_overrides      JSONB,
    relationship_overrides      JSONB,
    role_briefing_overrides     JSONB,
    role_persona_overrides      JSONB,
    organization_overrides      JSONB,                      -- sparse overrides of template.organizations by code

    status                      TEXT NOT NULL DEFAULT 'draft'
                                     CHECK (status IN ('draft','ready','archived')),
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by                  TEXT,

    CHECK (max_rounds > 0),
    CHECK (oil_price_start > 0),
    CHECK (array_length(active_theaters, 1) >= 1)
);

COMMENT ON TABLE  sim_scenarios IS
    'Scenario = sparse override of a template for a specific event. Validates max_rounds, oil_price, and theaters against the template''s allowed ranges (enforced at app layer and/or via triggers).';
COMMENT ON COLUMN sim_scenarios.country_stat_overrides IS
    'Sparse JSONB: {country_code: {stat: value, ...}} — only changed fields, falls back to template.default_country_stats.';
COMMENT ON COLUMN sim_scenarios.relationship_overrides IS
    'Sparse JSONB bilateral deltas; NULL = use template.default_relationships.';
COMMENT ON COLUMN sim_scenarios.unit_layout_id IS
    'NULL = use template.default_unit_layout_id.';
COMMENT ON COLUMN sim_scenarios.phase_a_duration_seconds IS
    'NULL = use template default phase A duration. Per DET_F, range [300, 1200] seconds.';
COMMENT ON COLUMN sim_scenarios.active_organizations IS
    'Subset of template.organizations[].code selected for this scenario. NULL = none active.';
COMMENT ON COLUMN sim_scenarios.organization_overrides IS
    'Sparse JSONB: {org_code: {...partial fields}} overriding template.organizations entries.';
COMMENT ON COLUMN sim_scenarios.role_assignments IS
    'DET_F §11.8 shape: [{role_code, active, binding}] where binding is a default hint only (final user→role binding happens at run time).';

CREATE INDEX idx_sim_scenarios_template ON sim_scenarios (template_id);
CREATE INDEX idx_sim_scenarios_status   ON sim_scenarios (status);
CREATE INDEX idx_sim_scenarios_layout   ON sim_scenarios (unit_layout_id)
    WHERE unit_layout_id IS NOT NULL;

-- =====================================================================
-- 4. SIM_RUNS (taxonomy extension)
-- =====================================================================
-- Runs are immutable executions of a scenario. They snapshot the merged
-- (template + scenario overrides) config at start time into run_config,
-- so even if the scenario or template is later edited the run remains
-- reproducible.
--
-- NOTE: The main sim_runs table lives in DET_B1_DATABASE_SCHEMA.sql.
-- This file provides the ALTER statements that integrate it with the
-- taxonomy model. If sim_runs does not yet exist when applying this
-- migration, it will be created with the minimal columns below.
-- ---------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS sim_runs (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status       TEXT NOT NULL DEFAULT 'pending'
                      CHECK (status IN ('pending','running','completed','aborted')),
    started_at   TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Add scenario_id FK (idempotent)
ALTER TABLE sim_runs
    ADD COLUMN IF NOT EXISTS scenario_id UUID REFERENCES sim_scenarios(id) ON DELETE RESTRICT;

-- Rename legacy sim_runs.config → run_config.
-- Semantic change: `config` held a loose runtime blob; `run_config` is the
-- frozen snapshot of the merged (template + scenario overrides) resolved
-- at run start. Wrapped in an IF EXISTS guard for idempotency.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'sim_runs' AND column_name = 'config'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'sim_runs' AND column_name = 'run_config'
    ) THEN
        EXECUTE 'ALTER TABLE sim_runs RENAME COLUMN config TO run_config';
    END IF;
END $$;

-- If neither column exists yet (fresh install), create run_config.
ALTER TABLE sim_runs
    ADD COLUMN IF NOT EXISTS run_config JSONB;

COMMENT ON COLUMN sim_runs.scenario_id IS
    'FK to the scenario this run executes. Restricted — cannot delete a scenario that has runs.';
COMMENT ON COLUMN sim_runs.run_config IS
    'Frozen snapshot of the merged (template + scenario overrides) config at run start. Immutable. Renamed from legacy sim_runs.config.';

-- DEPRECATION: sim_runs.max_rounds (if present in DET_B1 base schema) is
-- now redundant with run_config.resolved.max_rounds. Kept for now to
-- preserve backward compatibility; drop in a follow-up migration once
-- readers are migrated to run_config.resolved.max_rounds.
--
-- TODO: DET_B1 base schema defines current_round CHECK <= 8. This cap
-- should be removed so bounds defer to template.allowed_round_counts
-- (which may include 6, 8, or other values per scenario selection).

CREATE INDEX IF NOT EXISTS idx_sim_runs_scenario ON sim_runs (scenario_id);

-- =====================================================================
-- 5. FROZEN vs MUTABLE — REFERENCE NOTES
-- =====================================================================
--
-- Per Marat's 12 decisions (plan golden-nibbling-starlight.md, 2026-04-05):
--
-- TEMPLATE-LOCKED (scenario CANNOT override):
--   • map_config                 (map topology is the template)
--   • formula_coefficients       (Q3 — preserves calibration)
--   • allowed_round_counts       (the envelope itself)
--   • allowed_oil_price_range    (the envelope itself)
--   • allowed_theaters           (the envelope itself)
--   • Action catalog             (code-backed, Q-A)
--   • Event type taxonomy        (code-backed, Q-A)
--   • 4-block cognitive arch     (code-backed, Q-A)
--   • Round phase structure      (code-backed, Q-A)
--
-- SCENARIO-OVERRIDABLE (falls back to template when NULL):
--   • country_stat_overrides         (Q1 — free override)
--   • relationship_overrides         (Q2 — free override)
--   • unit_layout_id                 (Q4 — free override)
--   • role_briefing_overrides        (Q5 — free override)
--   • role_persona_overrides         (Q10 — free override)
--
-- SCENARIO-OWNED (no template default exists):
--   • event_metadata                 (venue, facilitator, participants)
--   • sim_starting_date              (Q7 — in-fiction starting date)
--   • max_rounds                     (Q9 — pick within template range)
--   • oil_price_start                (Q6 — pick within template range)
--   • phase_a_duration_seconds       (optional override of template default)
--   • active_theaters                (subset of template.allowed_theaters)
--   • active_organizations           (subset of template.organizations[].code)
--   • election_schedule              (Q7 — round numbers per election type)
--   • scripted_events                (Q7 — mandatory events per round)
--   • role_assignments               (which roles are active + who plays what)
--
-- SIM-RUN (immutable):
--   • run_config snapshots merged template+scenario at t₀
--   • All downstream state (round snapshots, event log, agent memories)
--     references sim_runs.id, never template/scenario directly.
--
-- =====================================================================
-- 6. VALIDATION HELPERS (optional triggers — TODO in follow-up migration)
-- =====================================================================
-- The following cross-table constraints are NOT enforced in this file:
--   • sim_scenarios.max_rounds IN sim_templates.allowed_round_counts
--   • sim_scenarios.oil_price_start <@ sim_templates.allowed_oil_price_range
--   • sim_scenarios.phase_a_duration_seconds <@ sim_templates.allowed_phase_a_duration_range
--   • sim_scenarios.active_theaters <@ sim_templates.allowed_theaters
--   • sim_scenarios.unit_layout_id.template_id = sim_scenarios.template_id
-- They should be added via BEFORE INSERT/UPDATE triggers in a follow-up
-- migration once the app-layer validation is stable.
--
-- =====================================================================
-- 7. RLS POLICY PLACEHOLDERS
-- =====================================================================
-- To be defined during Supabase migration:
--   • sim_templates        — read: all authed; write: admin/designer role only
--   • unit_layouts         — read: all authed; write: admin/designer role only
--   • layout_units         — read: all authed; write: admin/designer role only
--   • sim_scenarios        — read: all authed; write: facilitator role (own rows)
--   • sim_runs             — read: participants of that run; write: system only
--
-- TODO(supabase-migration): define RLS policies.
-- =====================================================================
