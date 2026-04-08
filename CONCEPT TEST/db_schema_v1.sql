-- =====================================================================
-- TTT — Map + Units DB Schema v1 (draft)
-- Target: PostgreSQL 15+ / Supabase
-- Version: 1.0 candidate (Template v1.0)
-- Date: 2026-04-05
--
-- Scope: map structure (global + theater grids), theater↔global linkage,
-- templates/scenarios/runs, units, and named layouts.
--
-- Natural keys (TEXT code) are kept alongside surrogate UUIDs so CSV
-- import/export (the current canonical data form) stays possible.
-- =====================================================================

-- ---------------------------------------------------------------------
-- Extensions
-- ---------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS "pgcrypto";     -- for gen_random_uuid()

-- ---------------------------------------------------------------------
-- 1. CORE REFERENCE TABLES
-- ---------------------------------------------------------------------

-- Countries: the 20 SIM nations (Columbia, Cathay, Sarmatia, …).
-- `code` is the natural key used everywhere in CSVs and engine code.
CREATE TABLE countries (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code         TEXT UNIQUE NOT NULL,             -- e.g. 'columbia'
    name         TEXT NOT NULL,                    -- e.g. 'Columbia'
    parallel     TEXT,                             -- real-world analogue
    regime_type  TEXT,                             -- democracy/autocracy/hybrid
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE  countries IS 'The 20 SIM countries. code is the canonical lowercase identifier.';
COMMENT ON COLUMN countries.code IS 'Natural key, lowercase, used across CSV and code.';

-- Theaters: local tactical maps attached to specific regions.
-- Currently 2: eastern_ereb (10×10), mashriq (10×10).
CREATE TABLE theaters (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code       TEXT UNIQUE NOT NULL,               -- e.g. 'eastern_ereb'
    name       TEXT NOT NULL,                      -- e.g. 'Eastern Ereb'
    rows       INT  NOT NULL CHECK (rows  > 0),
    cols       INT  NOT NULL CHECK (cols  > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE theaters IS 'Tactical theater grids attached to active war regions.';

-- ---------------------------------------------------------------------
-- 2. MAP STRUCTURE
-- ---------------------------------------------------------------------

-- Global map hex grid (10 rows × 20 cols).
-- One row per hex. (row, col) is the canonical TTT coord (row first, 1-indexed).
CREATE TABLE global_hexes (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    row              INT  NOT NULL CHECK (row BETWEEN 1 AND 10),
    col              INT  NOT NULL CHECK (col BETWEEN 1 AND 20),
    owner_code       TEXT REFERENCES countries(code),
    occupied_by_code TEXT REFERENCES countries(code),
    is_sea           BOOLEAN NOT NULL DEFAULT FALSE,
    is_chokepoint    BOOLEAN NOT NULL DEFAULT FALSE,
    chokepoint_name  TEXT,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (row, col),
    -- a country cannot occupy its own territory
    CHECK (occupied_by_code IS NULL OR occupied_by_code <> owner_code)
);
COMMENT ON TABLE  global_hexes IS 'The canonical 10x20 global hex grid.';
COMMENT ON COLUMN global_hexes.is_chokepoint IS 'Formosa Strait, Gulf Gate, Caribe Passage.';

CREATE INDEX idx_global_hexes_owner       ON global_hexes (owner_code);
CREATE INDEX idx_global_hexes_chokepoint  ON global_hexes (is_chokepoint) WHERE is_chokepoint;

-- Theater hex grid (10×10 currently for both eastern_ereb and mashriq).
-- (theater_code, row, col) is unique within each theater.
CREATE TABLE theater_hexes (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    theater_code     TEXT NOT NULL REFERENCES theaters(code),
    row              INT  NOT NULL CHECK (row BETWEEN 1 AND 10),
    col              INT  NOT NULL CHECK (col BETWEEN 1 AND 10),
    owner_code       TEXT REFERENCES countries(code),
    occupied_by_code TEXT REFERENCES countries(code),
    is_sea           BOOLEAN NOT NULL DEFAULT FALSE,
    is_die_hard      BOOLEAN NOT NULL DEFAULT FALSE,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (theater_code, row, col),
    CHECK (occupied_by_code IS NULL OR occupied_by_code <> owner_code)
);
COMMENT ON TABLE theater_hexes IS 'Per-theater tactical hex grids.';

CREATE INDEX idx_theater_hexes_owner ON theater_hexes (theater_code, owner_code);

-- ---------------------------------------------------------------------
-- 3. THEATER ↔ GLOBAL LINKAGE (canonical mapping)
-- ---------------------------------------------------------------------
--
-- Source of truth: Marat-approved FINAL v2 table (2026-04-05), documented
-- in CONCEPT TEST/CHANGES_LOG.md section 1. Each theater cell maps to
-- exactly ONE global hex. Multiple theater cells may share a global hex.
--
CREATE TABLE theater_global_links (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    theater_code   TEXT NOT NULL REFERENCES theaters(code),
    theater_row    INT  NOT NULL CHECK (theater_row BETWEEN 1 AND 10),
    theater_col    INT  NOT NULL CHECK (theater_col BETWEEN 1 AND 10),
    global_row     INT  NOT NULL CHECK (global_row BETWEEN 1 AND 10),
    global_col     INT  NOT NULL CHECK (global_col BETWEEN 1 AND 20),
    UNIQUE (theater_code, theater_row, theater_col)
);
COMMENT ON TABLE theater_global_links IS
    'Canonical theater cell -> global hex mapping. Part of the template.';

CREATE INDEX idx_tgl_global ON theater_global_links (global_row, global_col);

-- ---------------------------------------------------------------------
-- 4. TEMPLATES / SCENARIOS / RUNS
-- ---------------------------------------------------------------------
-- Hierarchy (per CHANGES_LOG canonical architecture):
--   sim_templates  (master — map + default placement + linkage rules)
--     └── sim_scenarios  (moderator-adjusted variants of a template)
--           └── sim_runs  (immutable executions of a scenario)
-- ---------------------------------------------------------------------

CREATE TABLE sim_templates (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT UNIQUE NOT NULL,              -- e.g. 'template_v1_0'
    description TEXT,
    version     TEXT,                              -- semver-ish, e.g. '1.0'
    map_config  JSONB,                             -- snapshot of dims + linkage
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by  TEXT
);
COMMENT ON TABLE sim_templates IS
    'Master SIM designs. Owns the map structure, theater linkage, and default unit placement.';

CREATE TABLE sim_scenarios (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID NOT NULL REFERENCES sim_templates(id) ON DELETE RESTRICT,
    name        TEXT NOT NULL,                     -- e.g. 'start_one'
    description TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by  TEXT,
    UNIQUE (template_id, name)
);
COMMENT ON TABLE sim_scenarios IS
    'Moderator-adjusted variants of a template. Cannot modify the map, only unit placement.';

CREATE TABLE sim_runs (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scenario_id  UUID NOT NULL REFERENCES sim_scenarios(id) ON DELETE RESTRICT,
    status       TEXT NOT NULL DEFAULT 'pending'
                      CHECK (status IN ('pending','running','completed','aborted')),
    started_at   TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);
COMMENT ON TABLE sim_runs IS 'Immutable executions of a scenario.';

CREATE INDEX idx_sim_scenarios_template ON sim_scenarios (template_id);
CREATE INDEX idx_sim_runs_scenario      ON sim_runs (scenario_id);

-- ---------------------------------------------------------------------
-- 5. UNITS
-- ---------------------------------------------------------------------
-- A unit belongs to EITHER:
--   (a) a scenario (moderator-adjusted placement), OR
--   (b) a template (the default layout for that template).
-- Exactly one of (scenario_id, template_id) must be set.
-- ---------------------------------------------------------------------

CREATE TABLE units (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scenario_id        UUID REFERENCES sim_scenarios(id) ON DELETE CASCADE,
    template_id        UUID REFERENCES sim_templates(id) ON DELETE CASCADE,
    unit_code          TEXT NOT NULL,              -- e.g. 'col_g_01'
    country_code       TEXT NOT NULL REFERENCES countries(code),
    unit_type          TEXT NOT NULL
                            CHECK (unit_type IN (
                                'ground','tactical_air','strategic_missile',
                                'air_defense','naval'
                            )),
    global_row         INT CHECK (global_row IS NULL OR global_row BETWEEN 1 AND 10),
    global_col         INT CHECK (global_col IS NULL OR global_col BETWEEN 1 AND 20),
    theater_code       TEXT REFERENCES theaters(code),
    theater_row        INT CHECK (theater_row IS NULL OR theater_row BETWEEN 1 AND 10),
    theater_col        INT CHECK (theater_col IS NULL OR theater_col BETWEEN 1 AND 10),
    embarked_on_unit_id UUID REFERENCES units(id) ON DELETE SET NULL,
    status             TEXT NOT NULL
                            CHECK (status IN ('active','reserve','embarked','destroyed')),
    notes              TEXT,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    -- exactly one owner (scenario XOR template)
    CHECK (
        (scenario_id IS NOT NULL)::int + (template_id IS NOT NULL)::int = 1
    ),
    -- if theater set, all three theater fields set together
    CHECK (
        (theater_code IS NULL AND theater_row IS NULL AND theater_col IS NULL)
        OR
        (theater_code IS NOT NULL AND theater_row IS NOT NULL AND theater_col IS NOT NULL)
    ),
    -- reserve/embarked units must NOT have global coords;
    -- active units MUST have global coords
    CHECK (
        (status = 'active' AND global_row IS NOT NULL AND global_col IS NOT NULL)
        OR
        (status IN ('reserve','embarked','destroyed'))
    ),
    -- embarked units must reference a carrier
    CHECK (
        (status = 'embarked' AND embarked_on_unit_id IS NOT NULL)
        OR
        (status <> 'embarked')
    )
);
COMMENT ON TABLE  units IS 'Unit entities. Lives under a template default OR a scenario.';
COMMENT ON COLUMN units.unit_code IS 'Natural key within scope (template or scenario).';

CREATE UNIQUE INDEX uq_units_scenario_code ON units (scenario_id, unit_code)
    WHERE scenario_id IS NOT NULL;
CREATE UNIQUE INDEX uq_units_template_code ON units (template_id, unit_code)
    WHERE template_id IS NOT NULL;
CREATE INDEX idx_units_scenario_country ON units (scenario_id, country_code)
    WHERE scenario_id IS NOT NULL;
CREATE INDEX idx_units_template_country ON units (template_id, country_code)
    WHERE template_id IS NOT NULL;
CREATE INDEX idx_units_global_hex       ON units (global_row, global_col);
CREATE INDEX idx_units_theater_cell     ON units (theater_code, theater_row, theater_col)
    WHERE theater_code IS NOT NULL;

-- ---------------------------------------------------------------------
-- 6. LAYOUTS (named deployment snapshots)
-- ---------------------------------------------------------------------
-- Layouts are portable saved unit placements — candidates for becoming
-- a template default OR a scenario variant. They reference units by
-- natural key (unit_code) instead of UUID so they can be exported to
-- CSV and re-imported later.
-- ---------------------------------------------------------------------

CREATE TABLE layouts (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT NOT NULL,                     -- e.g. 'start_one'
    template_id UUID REFERENCES sim_templates(id) ON DELETE SET NULL,
    description TEXT,
    unit_count  INT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by  TEXT,
    UNIQUE (template_id, name)
);
COMMENT ON TABLE layouts IS
    'Named deployment snapshots. Portable (unit_code based) candidates for template defaults or scenario variants.';

CREATE TABLE layout_units (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    layout_id        UUID NOT NULL REFERENCES layouts(id) ON DELETE CASCADE,
    unit_code        TEXT NOT NULL,
    country_code     TEXT NOT NULL,
    unit_type        TEXT NOT NULL
                          CHECK (unit_type IN (
                              'ground','tactical_air','strategic_missile',
                              'air_defense','naval'
                          )),
    global_row       INT CHECK (global_row IS NULL OR global_row BETWEEN 1 AND 10),
    global_col       INT CHECK (global_col IS NULL OR global_col BETWEEN 1 AND 20),
    theater_code     TEXT,
    theater_row      INT CHECK (theater_row IS NULL OR theater_row BETWEEN 1 AND 10),
    theater_col      INT CHECK (theater_col IS NULL OR theater_col BETWEEN 1 AND 10),
    embarked_on_code TEXT,                         -- unit_code of carrier, not UUID
    status           TEXT NOT NULL
                          CHECK (status IN ('active','reserve','embarked','destroyed')),
    notes            TEXT,
    UNIQUE (layout_id, unit_code)
);
COMMENT ON COLUMN layout_units.embarked_on_code IS
    'Carrier unit_code (natural key) — enables CSV round-tripping across DBs.';

CREATE INDEX idx_layout_units_layout ON layout_units (layout_id);

-- =====================================================================
-- SEED DATA
-- =====================================================================

-- ---------------------------------------------------------------------
-- Theaters
-- ---------------------------------------------------------------------
INSERT INTO theaters (code, name, rows, cols) VALUES
    ('eastern_ereb', 'Eastern Ereb', 10, 10),
    ('mashriq',      'Mashriq',      10, 10);

-- ---------------------------------------------------------------------
-- Countries (20) — values match 2 SEED/C_MECHANICS/C4_DATA/countries.csv
-- ---------------------------------------------------------------------
INSERT INTO countries (code, name, parallel, regime_type) VALUES
    ('columbia', 'Columbia', 'United States',      'democracy'),
    ('cathay',   'Cathay',   'China',              'autocracy'),
    ('sarmatia', 'Sarmatia', 'Russia',             'autocracy'),
    ('ruthenia', 'Ruthenia', 'Ukraine',            'democracy'),
    ('persia',   'Persia',   'Iran',               'hybrid'),
    ('gallia',   'Gallia',   'France',             'democracy'),
    ('teutonia', 'Teutonia', 'Germany',            'democracy'),
    ('freeland', 'Freeland', 'Poland',             'democracy'),
    ('ponte',    'Ponte',    'Italy',              'democracy'),
    ('albion',   'Albion',   'United Kingdom',     'democracy'),
    ('bharata',  'Bharata',  'India',              'democracy'),
    ('levantia', 'Levantia', 'Israel',             'democracy'),
    ('formosa',  'Formosa',  'Taiwan',             'democracy'),
    ('phrygia',  'Phrygia',  'Turkey',             'hybrid'),
    ('yamato',   'Yamato',   'Japan',              'democracy'),
    ('solaria',  'Solaria',  'Saudi Arabia',       'autocracy'),
    ('choson',   'Choson',   'North Korea',        'autocracy'),
    ('hanguk',   'Hanguk',   'South Korea',        'democracy'),
    ('caribe',   'Caribe',   'Cuba + Venezuela',   'autocracy'),
    ('mirage',   'Mirage',   'UAE',                'autocracy');

-- ---------------------------------------------------------------------
-- Chokepoints — derived from SEED_C1_MAP_GLOBAL_STATE_v4.json
-- (canonical 1-indexed coords per CHANGES_LOG 2026-04-04)
-- ---------------------------------------------------------------------
-- NOTE: global_hexes row inserts for the full 10x20 grid are out of
-- scope for this draft; only the chokepoint flags are seeded here.
-- Full grid seeding is a separate migration, driven by the JSON state.
INSERT INTO global_hexes (row, col, is_sea, is_chokepoint, chokepoint_name) VALUES
    (7,  17, TRUE, TRUE, 'Formosa Strait'),
    (8,  12, TRUE, TRUE, 'Gulf Gate'),
    (8,   4, TRUE, TRUE, 'Caribe Passage')
ON CONFLICT (row, col) DO UPDATE
    SET is_chokepoint   = EXCLUDED.is_chokepoint,
        chokepoint_name = EXCLUDED.chokepoint_name,
        is_sea          = EXCLUDED.is_sea;

-- ---------------------------------------------------------------------
-- Theater ↔ Global linkage — canonical FINAL v2 table (Marat 2026-04-05)
-- ---------------------------------------------------------------------
-- Eastern Ereb: 10×10 = 100 cells. Rules:
--   rows 1-4, owner=sarmatia → (3,12)
--   rows 5-10, owner=sarmatia → (4,12)
--   owner=ruthenia any row → (4,11)
--   sea cells → (5,12)
-- Mashriq: 10×10 = 100 cells. Rules per CHANGES_LOG table.
--
-- NOTE: per-cell rows must be generated from the theater JSONs
-- (SEED_C3_THEATER_EASTERN_EREB_STATE_v3.json +
--  SEED_C3_THEATER_MASHRIQ_STATE_v1.json) at import time — each JSON
-- carries per-hex owner/is_sea which determines the global_link.
--
-- The INSERT approach below is a DO-block sketch; the actual seed
-- should be produced by a build script that reads the theater JSONs.
-- Kept here as documentation of the seeding rules.
--
-- Example (sketch — replace with generated full mapping):
--
-- INSERT INTO theater_global_links (theater_code, theater_row, theater_col, global_row, global_col) VALUES
--     ('eastern_ereb', 1, 1, 3, 12),  -- sarmatia rows 1-4
--     ('eastern_ereb', 5, 1, 4, 12),  -- sarmatia rows 5+
--     ('eastern_ereb', 3, 5, 4, 11),  -- ruthenia
--     ('eastern_ereb', 8, 6, 5, 12),  -- sea
--     …;
-- ---------------------------------------------------------------------
-- TODO(seed-script): generate ~200 rows from theater JSONs.

-- ---------------------------------------------------------------------
-- Default template: Template v1.0
-- ---------------------------------------------------------------------
INSERT INTO sim_templates (name, description, version) VALUES
    ('template_v1_0',
     'TTT Template v1.0 — canonical map + theater linkage v2 + default unit placement (2026-04-05).',
     '1.0');

-- =====================================================================
-- NOTES
-- =====================================================================
-- - RLS policies to be added during Supabase migration (moderator/player
--   roles, scenario-scoped reads/writes).
-- - Natural keys (code) kept alongside surrogate UUIDs to enable
--   CSV import/export and bidirectional sync with SEED data files.
-- - Canonical coord convention: (row, col), row first, 1-indexed.
--   Global grid: [1..10] × [1..20]. Theater grids: [1..10] × [1..10].
-- - Self-occupation forbidden by CHECK constraints
--   (country cannot occupy its own territory).
-- - Units table invariants enforced in-DB:
--     • active ⇒ global coords set
--     • reserve/embarked/destroyed ⇒ global coords optional
--     • embarked ⇒ embarked_on_unit_id set
--     • theater fields are all-or-nothing
-- =====================================================================
