-- =====================================================================
-- TTT — Scenario "start_one" Seed
-- File: CONCEPT TEST/scenario_start_one_seed.sql
-- Target: PostgreSQL 15+ / Supabase
-- Date: 2026-04-05
--
-- Prereqs:
--   1. DET_B1a_TEMPLATE_TAXONOMY.sql applied
--   2. template_v1_0_seed.sql applied (ttt_v1_0 template must exist)
--
-- Seeds:
--   1. Unit layout 'start_one' — 345 units from start_one.csv
--      (verified identical to units.csv on 2026-04-05 via diff)
--   2. Scenario 'start_one' — references ttt_v1_0 template, uses
--      start_one layout, no other overrides (pure template defaults).
--
-- Data-fidelity note:
--   As of 2026-04-05, start_one.csv and units.csv are byte-identical.
--   This seed therefore clones the template's default_unit_layout into
--   a separately-named layout owned by the start_one scenario. If
--   Marat later diverges start_one.csv from units.csv, regenerate by
--   replacing the INSERT ... SELECT clone with explicit VALUES rows.
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. Create start_one unit layout
-- ---------------------------------------------------------------------
INSERT INTO unit_layouts (code, name, template_id, description, unit_count, created_by) VALUES (
    'start_one',
    'Start One - Marat-reviewed canonical layout',
    (SELECT id FROM sim_templates WHERE code = 'ttt_v1_0'),
    'Hand-reviewed by Marat 2026-04-05, 345 units. Identical to template_v1_0_default as of this date (see units_layouts/start_one.csv).',
    345,
    'marat'
);

-- ---------------------------------------------------------------------
-- 2. Clone layout_units from template default into start_one
-- ---------------------------------------------------------------------
INSERT INTO layout_units (layout_id, unit_code, country_code, unit_type, global_row, global_col, theater, theater_row, theater_col, embarked_on, status, notes)
SELECT
    (SELECT id FROM unit_layouts WHERE code = 'start_one') AS layout_id,
    unit_code, country_code, unit_type, global_row, global_col, theater, theater_row, theater_col, embarked_on, status, notes
FROM layout_units
WHERE layout_id = (SELECT id FROM unit_layouts WHERE code = 'template_v1_0_default');

-- ---------------------------------------------------------------------
-- 3. Insert start_one scenario
-- ---------------------------------------------------------------------
INSERT INTO sim_scenarios (
    template_id,
    code,
    name,
    event_metadata,
    sim_starting_date,
    max_rounds,
    oil_price_start,
    phase_a_duration_seconds,
    active_theaters,
    election_schedule,
    scripted_events,
    role_assignments,
    unit_layout_id,
    country_stat_overrides,
    relationship_overrides,
    role_briefing_overrides,
    role_persona_overrides,
    status,
    created_by
) VALUES (
    (SELECT id FROM sim_templates WHERE code = 'ttt_v1_0'),
    'start_one',
    'Start One - initial reviewed deployment',

    -- event_metadata
    '{
      "event_name": "Internal test",
      "venue": "n/a",
      "facilitator_ids": [],
      "participant_count": 0,
      "participant_profile": "ai_only",
      "delivery_format": "remote",
      "learning_objectives": ["validate template v1.0", "unmanned spacecraft bring-up"]
    }'::jsonb,

    '2026-01-01'::date,
    6,
    80.0,
    NULL,                                        -- phase_a_duration_seconds: use template default
    ARRAY['eastern_ereb','mashriq']::TEXT[],
    NULL,                                        -- election_schedule (defer)
    NULL,                                        -- scripted_events (defer)
    NULL,                                        -- role_assignments (defer)
    (SELECT id FROM unit_layouts WHERE code = 'start_one'),

    -- Sparse overrides: all NULL for start_one (pure template defaults)
    NULL,                                        -- country_stat_overrides
    NULL,                                        -- relationship_overrides
    NULL,                                        -- role_briefing_overrides
    NULL,                                        -- role_persona_overrides

    'draft',
    'marat'
);

-- ---------------------------------------------------------------------
-- Verification queries (run manually after seed)
-- ---------------------------------------------------------------------
-- SELECT COUNT(*) FROM layout_units
--   WHERE layout_id = (SELECT id FROM unit_layouts WHERE code = 'start_one');
-- Expected: 345
--
-- SELECT s.code, s.name, t.code AS template_code, l.code AS layout_code, s.max_rounds, s.oil_price_start, s.active_theaters
-- FROM sim_scenarios s
-- JOIN sim_templates t ON s.template_id = t.id
-- LEFT JOIN unit_layouts l ON s.unit_layout_id = l.id
-- WHERE s.code = 'start_one';
-- =====================================================================
