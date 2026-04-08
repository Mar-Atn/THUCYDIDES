-- =====================================================================
-- TTT — Template v1.0 Seed
-- File: CONCEPT TEST/template_v1_0_seed.sql
-- Target: PostgreSQL 15+ / Supabase
-- Date: 2026-04-05
--
-- Prereqs:
--   1. DET_B1_DATABASE_SCHEMA.sql applied (countries, theaters tables)
--   2. DET_B1a_TEMPLATE_TAXONOMY.sql applied (sim_templates, unit_layouts, layout_units)
--
-- Seeds:
--   1. Template 'ttt_v1_0' — "TTT Power Transition 2026"
--   2. Unit layout 'template_v1_0_default' — 345 units from units.csv
--   3. Links template → default layout
--
-- Source data:
--   • 2 SEED/C_MECHANICS/C4_DATA/countries.csv (20 countries)
--   • 2 SEED/C_MECHANICS/C4_DATA/units.csv (345 units)
--
-- Data-fidelity notes:
--   • default_country_stats JSONB is derived directly from countries.csv v1.0
--   • formula_coefficients is a PLACEHOLDER — countries.csv has no explicit
--     sanctions_coefficient/tariff_coefficient columns. Actual coefficients
--     live in Python engine code (parameter review 15/15, 2026-04-02).
--     TODO(reconcile): extract from app/engine and embed in template.
--   • default_relationships JSONB is a PLACEHOLDER pointer to relationships.csv.
--     TODO(reconcile): convert relationships.csv to canonical JSONB shape.
--   • default_role_briefings JSONB is a PLACEHOLDER pointer to roles.csv.
--     TODO(reconcile): assemble per-role briefings from roles.csv + persona docs.
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. Insert Template v1.0
-- ---------------------------------------------------------------------
INSERT INTO sim_templates (
    code, name, version, description, status,
    map_config,
    default_country_stats,
    default_relationships,
    default_role_briefings,
    formula_coefficients,
    organizations,
    allowed_round_counts,
    allowed_oil_price_range,
    allowed_phase_a_duration_range,
    allowed_theaters,
    created_by
) VALUES (
    'ttt_v1_0',
    'TTT Power Transition 2026',
    '1.0',
    'Canonical TTT template locked 2026-04-05 after Map+Units finalization. 20 countries, 10x20 global hex grid, 2 tactical theaters (eastern_ereb, mashriq), 345 default units.',
    'published',

    -- map_config
    '{
      "global": {"rows": 10, "cols": 20},
      "theaters": {
        "eastern_ereb": {"rows": 10, "cols": 10},
        "mashriq":      {"rows": 10, "cols": 10}
      },
      "linkage_source": "SEED_C3_THEATER_*_STATE_v*.json + CHANGES_LOG 2026-04-05 v2",
      "chokepoints": [
        {"name": "Formosa Strait", "row": 7, "col": 17},
        {"name": "Gulf Gate",      "row": 8, "col": 12},
        {"name": "Caribe Passage", "row": 8, "col": 4}
      ]
    }'::jsonb,

    -- default_country_stats (derived from countries.csv v1.0)
    '{
      "columbia": {"parallel":"United States","regime_type":"democracy","team_type":"team","team_size_min":7,"team_size_max":9,"ai_default":false,"gdp":280,"gdp_growth_base":1.8,"sector_resources":8,"sector_industry":18,"sector_services":55,"sector_technology":22,"tax_rate":0.24,"treasury":30,"inflation":3.5,"trade_balance":-12,"oil_producer":true,"opec_member":false,"opec_production":"na","formosa_dependency":0.65,"debt_burden":1.25,"social_baseline":0.30,"oil_production_mbpd":13,"mil_ground":22,"mil_naval":11,"mil_tactical_air":15,"mil_strategic_missiles":12,"mil_air_defense":6,"prod_cost_ground":3,"prod_cost_naval":5,"prod_cost_tactical":4,"prod_cap_ground":4,"prod_cap_naval":2,"prod_cap_tactical":3,"maintenance_per_unit":0.051,"strategic_missile_growth":0.5,"mobilization_pool":0,"stability":7,"political_support":38,"dem_rep_split_dem":52,"dem_rep_split_rep":48,"war_tiredness":1,"nuclear_level":3,"nuclear_rd_progress":1.0,"ai_level":3,"ai_rd_progress":0.50,"at_war_with":["persia"],"home_zones":["col_nw","col_w","col_main_1","col_main_2","col_main_3","col_main_4","col_south"]},
      "cathay":   {"parallel":"China","regime_type":"autocracy","team_type":"team","team_size_min":5,"team_size_max":5,"ai_default":false,"gdp":190,"gdp_growth_base":4.0,"sector_resources":5,"sector_industry":52,"sector_services":30,"sector_technology":13,"tax_rate":0.25,"treasury":50,"inflation":0.5,"trade_balance":12,"oil_producer":false,"opec_member":false,"opec_production":"na","formosa_dependency":0.25,"debt_burden":0.55,"social_baseline":0.20,"oil_production_mbpd":0,"mil_ground":25,"mil_naval":7,"mil_tactical_air":12,"mil_strategic_missiles":4,"mil_air_defense":3,"prod_cost_ground":2,"prod_cost_naval":4,"prod_cost_tactical":3,"prod_cap_ground":5,"prod_cap_naval":1,"prod_cap_tactical":3,"maintenance_per_unit":0.021,"strategic_missile_growth":1,"mobilization_pool":3,"stability":8,"political_support":58,"dem_rep_split_dem":0,"dem_rep_split_rep":0,"war_tiredness":0,"nuclear_level":2,"nuclear_rd_progress":0.80,"ai_level":3,"ai_rd_progress":0.30,"at_war_with":[],"home_zones":["cathay_1","cathay_2","cathay_3","cathay_4","cathay_5","cathay_6","cathay_7"]},
      "sarmatia": {"parallel":"Russia","regime_type":"autocracy","team_type":"team","team_size_min":3,"team_size_max":4,"ai_default":false,"gdp":20,"gdp_growth_base":1.0,"sector_resources":40,"sector_industry":25,"sector_services":25,"sector_technology":10,"tax_rate":0.20,"treasury":18,"inflation":5.0,"trade_balance":2,"oil_producer":true,"opec_member":true,"opec_production":"normal","formosa_dependency":0.15,"debt_burden":0.25,"social_baseline":0.25,"oil_production_mbpd":10,"mil_ground":18,"mil_naval":2,"mil_tactical_air":8,"mil_strategic_missiles":12,"mil_air_defense":3,"prod_cost_ground":1.5,"prod_cost_naval":4,"prod_cost_tactical":3,"prod_cap_ground":4,"prod_cap_naval":0,"prod_cap_tactical":2,"maintenance_per_unit":0.006,"strategic_missile_growth":0,"mobilization_pool":12,"stability":5,"political_support":55,"dem_rep_split_dem":0,"dem_rep_split_rep":0,"war_tiredness":4,"nuclear_level":3,"nuclear_rd_progress":1.0,"ai_level":1,"ai_rd_progress":0.30,"at_war_with":["ruthenia"],"home_zones":["nord_n1","nord_w1","nord_c1","nord_e1","nord_e2","nord_e3","nord_w2","nord_c2"]},
      "ruthenia": {"parallel":"Ukraine","regime_type":"democracy","team_type":"team","team_size_min":3,"team_size_max":3,"ai_default":false,"gdp":2.2,"gdp_growth_base":2.5,"sector_resources":15,"sector_industry":20,"sector_services":40,"sector_technology":10,"tax_rate":0.25,"treasury":5,"inflation":7.5,"trade_balance":-0.8,"oil_producer":false,"opec_member":false,"opec_production":"na","formosa_dependency":0.10,"debt_burden":0.30,"social_baseline":0.20,"oil_production_mbpd":0,"mil_ground":11,"mil_naval":0,"mil_tactical_air":3,"mil_strategic_missiles":0,"mil_air_defense":1,"prod_cost_ground":0.5,"prod_cost_naval":0,"prod_cost_tactical":1,"prod_cap_ground":2,"prod_cap_naval":0,"prod_cap_tactical":1,"maintenance_per_unit":0.003,"strategic_missile_growth":0,"mobilization_pool":5,"stability":5,"political_support":52,"dem_rep_split_dem":0,"dem_rep_split_rep":0,"war_tiredness":4,"nuclear_level":0,"nuclear_rd_progress":0.0,"ai_level":1,"ai_rd_progress":0.40,"at_war_with":["sarmatia"],"home_zones":["ruthenia_1","ruthenia_2"]},
      "persia":   {"parallel":"Iran","regime_type":"hybrid","team_type":"team","team_size_min":3,"team_size_max":3,"ai_default":false,"gdp":5,"gdp_growth_base":0.5,"sector_resources":35,"sector_industry":30,"sector_services":28,"sector_technology":7,"tax_rate":0.18,"treasury":1,"inflation":50.0,"trade_balance":-1,"oil_producer":true,"opec_member":true,"opec_production":"normal","formosa_dependency":0.15,"debt_burden":0,"social_baseline":0.20,"oil_production_mbpd":3.5,"mil_ground":8,"mil_naval":0,"mil_tactical_air":6,"mil_strategic_missiles":0,"mil_air_defense":1,"prod_cost_ground":1,"prod_cost_naval":2,"prod_cost_tactical":2,"prod_cap_ground":2,"prod_cap_naval":0,"prod_cap_tactical":1,"maintenance_per_unit":0.003,"strategic_missile_growth":0,"mobilization_pool":5,"stability":4,"political_support":40,"dem_rep_split_dem":0,"dem_rep_split_rep":0,"war_tiredness":1,"nuclear_level":0,"nuclear_rd_progress":0.70,"ai_level":0,"ai_rd_progress":0.10,"at_war_with":["columbia","levantia"],"home_zones":["persia_1","persia_2","persia_3"]},
      "gallia":   {"parallel":"France","regime_type":"democracy","team_type":"europe","team_size_min":1,"team_size_max":1,"ai_default":false,"gdp":34,"gdp_growth_base":1.0,"sector_resources":5,"sector_industry":20,"sector_services":55,"sector_technology":20,"tax_rate":0.45,"treasury":8,"inflation":2.5,"trade_balance":-1,"oil_producer":false,"opec_member":false,"opec_production":"na","formosa_dependency":0.35,"debt_burden":1.10,"social_baseline":0.35,"oil_production_mbpd":0,"mil_ground":6,"mil_naval":1,"mil_tactical_air":4,"mil_strategic_missiles":2,"mil_air_defense":1,"prod_cost_ground":3,"prod_cost_naval":5,"prod_cost_tactical":4,"prod_cap_ground":2,"prod_cap_naval":0,"prod_cap_tactical":1,"maintenance_per_unit":0.016,"strategic_missile_growth":0,"mobilization_pool":0,"stability":7,"political_support":40,"dem_rep_split_dem":0,"dem_rep_split_rep":0,"war_tiredness":0,"nuclear_level":2,"nuclear_rd_progress":0.80,"ai_level":2,"ai_rd_progress":0.30,"at_war_with":[],"home_zones":["gallia_1","gallia_2"]},
      "teutonia": {"parallel":"Germany","regime_type":"democracy","team_type":"europe","team_size_min":1,"team_size_max":1,"ai_default":false,"gdp":45,"gdp_growth_base":1.2,"sector_resources":3,"sector_industry":28,"sector_services":50,"sector_technology":19,"tax_rate":0.38,"treasury":12,"inflation":2.5,"trade_balance":3,"oil_producer":false,"opec_member":false,"opec_production":"na","formosa_dependency":0.45,"debt_burden":0.65,"social_baseline":0.30,"oil_production_mbpd":0,"mil_ground":6,"mil_naval":0,"mil_tactical_air":3,"mil_strategic_missiles":0,"mil_air_defense":1,"prod_cost_ground":2.5,"prod_cost_naval":4,"prod_cost_tactical":3.5,"prod_cap_ground":2,"prod_cap_naval":0,"prod_cap_tactical":1,"maintenance_per_unit":0.020,"strategic_missile_growth":0,"mobilization_pool":0,"stability":7,"political_support":45,"dem_rep_split_dem":0,"dem_rep_split_rep":0,"war_tiredness":0,"nuclear_level":0,"nuclear_rd_progress":0.10,"ai_level":2,"ai_rd_progress":0.20,"at_war_with":[],"home_zones":["teutonia_1","teutonia_2"]},
      "freeland": {"parallel":"Poland","regime_type":"democracy","team_type":"europe","team_size_min":1,"team_size_max":1,"ai_default":false,"gdp":9,"gdp_growth_base":3.7,"sector_resources":8,"sector_industry":30,"sector_services":50,"sector_technology":12,"tax_rate":0.35,"treasury":4,"inflation":4.0,"trade_balance":0,"oil_producer":false,"opec_member":false,"opec_production":"na","formosa_dependency":0.25,"debt_burden":0.50,"social_baseline":0.25,"oil_production_mbpd":0,"mil_ground":5,"mil_naval":0,"mil_tactical_air":2,"mil_strategic_missiles":0,"mil_air_defense":1,"prod_cost_ground":2,"prod_cost_naval":3,"prod_cost_tactical":3,"prod_cap_ground":2,"prod_cap_naval":0,"prod_cap_tactical":1,"maintenance_per_unit":0.015,"strategic_missile_growth":0,"mobilization_pool":0,"stability":8,"political_support":55,"dem_rep_split_dem":0,"dem_rep_split_rep":0,"war_tiredness":0,"nuclear_level":0,"nuclear_rd_progress":0.0,"ai_level":1,"ai_rd_progress":0.40,"at_war_with":[],"home_zones":["freeland"]},
      "ponte":    {"parallel":"Italy","regime_type":"democracy","team_type":"europe","team_size_min":1,"team_size_max":1,"ai_default":false,"gdp":22,"gdp_growth_base":0.8,"sector_resources":4,"sector_industry":22,"sector_services":60,"sector_technology":14,"tax_rate":0.40,"treasury":4,"inflation":2.5,"trade_balance":0,"oil_producer":false,"opec_member":false,"opec_production":"na","formosa_dependency":0.30,"debt_burden":1.30,"social_baseline":0.30,"oil_production_mbpd":0,"mil_ground":4,"mil_naval":0,"mil_tactical_air":2,"mil_strategic_missiles":0,"mil_air_defense":0,"prod_cost_ground":2.5,"prod_cost_naval":4.5,"prod_cost_tactical":3.5,"prod_cap_ground":1,"prod_cap_naval":0,"prod_cap_tactical":1,"maintenance_per_unit":0.018,"strategic_missile_growth":0,"mobilization_pool":0,"stability":6,"political_support":42,"dem_rep_split_dem":0,"dem_rep_split_rep":0,"war_tiredness":0,"nuclear_level":0,"nuclear_rd_progress":0.0,"ai_level":1,"ai_rd_progress":0.30,"at_war_with":[],"home_zones":["ponte"]},
      "albion":   {"parallel":"United Kingdom","regime_type":"democracy","team_type":"europe","team_size_min":1,"team_size_max":1,"ai_default":false,"gdp":33,"gdp_growth_base":1.1,"sector_resources":5,"sector_industry":17,"sector_services":60,"sector_technology":18,"tax_rate":0.35,"treasury":8,"inflation":3.0,"trade_balance":-2,"oil_producer":false,"opec_member":false,"opec_production":"na","formosa_dependency":0.40,"debt_burden":1.00,"social_baseline":0.30,"oil_production_mbpd":0,"mil_ground":4,"mil_naval":2,"mil_tactical_air":3,"mil_strategic_missiles":2,"mil_air_defense":2,"prod_cost_ground":3,"prod_cost_naval":5,"prod_cost_tactical":4,"prod_cap_ground":1,"prod_cap_naval":0,"prod_cap_tactical":1,"maintenance_per_unit":0.020,"strategic_missile_growth":0,"mobilization_pool":0,"stability":7,"political_support":38,"dem_rep_split_dem":0,"dem_rep_split_rep":0,"war_tiredness":0,"nuclear_level":2,"nuclear_rd_progress":0.70,"ai_level":2,"ai_rd_progress":0.40,"at_war_with":[],"home_zones":["albion"]},
      "bharata":  {"parallel":"India","regime_type":"democracy","team_type":"solo","team_size_min":1,"team_size_max":1,"ai_default":true,"gdp":42,"gdp_growth_base":6.5,"sector_resources":10,"sector_industry":25,"sector_services":48,"sector_technology":17,"tax_rate":0.28,"treasury":12,"inflation":5.0,"trade_balance":-3,"oil_producer":false,"opec_member":false,"opec_production":"na","formosa_dependency":0.35,"debt_burden":0.85,"social_baseline":0.20,"oil_production_mbpd":0,"mil_ground":12,"mil_naval":2,"mil_tactical_air":4,"mil_strategic_missiles":0,"mil_air_defense":2,"prod_cost_ground":2,"prod_cost_naval":4,"prod_cost_tactical":3,"prod_cap_ground":3,"prod_cap_naval":0.5,"prod_cap_tactical":1,"maintenance_per_unit":0.016,"strategic_missile_growth":0,"mobilization_pool":0,"stability":6,"political_support":58,"dem_rep_split_dem":0,"dem_rep_split_rep":0,"war_tiredness":0,"nuclear_level":1,"nuclear_rd_progress":0.40,"ai_level":2,"ai_rd_progress":0.45,"at_war_with":[],"home_zones":["bharata_1","bharata_2","bharata_3"]},
      "levantia": {"parallel":"Israel","regime_type":"democracy","team_type":"solo","team_size_min":1,"team_size_max":1,"ai_default":true,"gdp":5,"gdp_growth_base":3.0,"sector_resources":3,"sector_industry":15,"sector_services":50,"sector_technology":32,"tax_rate":0.52,"treasury":10,"inflation":3.5,"trade_balance":-1,"oil_producer":false,"opec_member":false,"opec_production":"na","formosa_dependency":0.30,"debt_burden":0.60,"social_baseline":0.28,"oil_production_mbpd":0,"mil_ground":6,"mil_naval":0,"mil_tactical_air":4,"mil_strategic_missiles":3,"mil_air_defense":3,"prod_cost_ground":3,"prod_cost_naval":5,"prod_cost_tactical":4,"prod_cap_ground":2,"prod_cap_naval":0,"prod_cap_tactical":2,"maintenance_per_unit":0.011,"strategic_missile_growth":0,"mobilization_pool":0,"stability":5,"political_support":52,"dem_rep_split_dem":0,"dem_rep_split_rep":0,"war_tiredness":2,"nuclear_level":1,"nuclear_rd_progress":0.50,"ai_level":2,"ai_rd_progress":0.55,"at_war_with":["persia"],"home_zones":["levantia"]},
      "formosa":  {"parallel":"Taiwan","regime_type":"democracy","team_type":"solo","team_size_min":1,"team_size_max":1,"ai_default":true,"gdp":8,"gdp_growth_base":3.0,"sector_resources":2,"sector_industry":30,"sector_services":35,"sector_technology":33,"tax_rate":0.40,"treasury":15,"inflation":2.0,"trade_balance":4,"oil_producer":false,"opec_member":false,"opec_production":"na","formosa_dependency":0.0,"debt_burden":0.30,"social_baseline":0.22,"oil_production_mbpd":0,"mil_ground":4,"mil_naval":0,"mil_tactical_air":3,"mil_strategic_missiles":0,"mil_air_defense":2,"prod_cost_ground":3,"prod_cost_naval":5,"prod_cost_tactical":4,"prod_cap_ground":1,"prod_cap_naval":0,"prod_cap_tactical":1,"maintenance_per_unit":0.007,"strategic_missile_growth":0,"mobilization_pool":0,"stability":7,"political_support":55,"dem_rep_split_dem":0,"dem_rep_split_rep":0,"war_tiredness":0,"nuclear_level":0,"nuclear_rd_progress":0.0,"ai_level":2,"ai_rd_progress":0.50,"at_war_with":[],"home_zones":["formosa"]},
      "phrygia":  {"parallel":"Turkey","regime_type":"hybrid","team_type":"solo","team_size_min":1,"team_size_max":1,"ai_default":true,"gdp":11,"gdp_growth_base":3.0,"sector_resources":8,"sector_industry":30,"sector_services":50,"sector_technology":12,"tax_rate":0.25,"treasury":4,"inflation":45.0,"trade_balance":-3,"oil_producer":false,"opec_member":false,"opec_production":"na","formosa_dependency":0.20,"debt_burden":0.35,"social_baseline":0.22,"oil_production_mbpd":0,"mil_ground":6,"mil_naval":1,"mil_tactical_air":3,"mil_strategic_missiles":0,"mil_air_defense":1,"prod_cost_ground":2,"prod_cost_naval":4,"prod_cost_tactical":3,"prod_cap_ground":2,"prod_cap_naval":0,"prod_cap_tactical":1,"maintenance_per_unit":0.007,"strategic_missile_growth":0,"mobilization_pool":0,"stability":5,"political_support":50,"dem_rep_split_dem":0,"dem_rep_split_rep":0,"war_tiredness":0,"nuclear_level":0,"nuclear_rd_progress":0.0,"ai_level":1,"ai_rd_progress":0.25,"at_war_with":[],"home_zones":["phrygia_1","phrygia_2"]},
      "yamato":   {"parallel":"Japan","regime_type":"democracy","team_type":"solo","team_size_min":1,"team_size_max":1,"ai_default":true,"gdp":43,"gdp_growth_base":1.0,"sector_resources":2,"sector_industry":28,"sector_services":50,"sector_technology":20,"tax_rate":0.30,"treasury":15,"inflation":2.5,"trade_balance":-2,"oil_producer":false,"opec_member":false,"opec_production":"na","formosa_dependency":0.55,"debt_burden":2.50,"social_baseline":0.30,"oil_production_mbpd":0,"mil_ground":3,"mil_naval":2,"mil_tactical_air":3,"mil_strategic_missiles":0,"mil_air_defense":2,"prod_cost_ground":3,"prod_cost_naval":5,"prod_cost_tactical":4,"prod_cap_ground":1,"prod_cap_naval":0,"prod_cap_tactical":1,"maintenance_per_unit":0.012,"strategic_missile_growth":0,"mobilization_pool":0,"stability":8,"political_support":48,"dem_rep_split_dem":0,"dem_rep_split_rep":0,"war_tiredness":0,"nuclear_level":0,"nuclear_rd_progress":0.00,"ai_level":3,"ai_rd_progress":0.30,"at_war_with":[],"home_zones":["yamato_1","yamato_2"]},
      "solaria":  {"parallel":"Saudi Arabia","regime_type":"autocracy","team_type":"solo","team_size_min":1,"team_size_max":1,"ai_default":true,"gdp":11,"gdp_growth_base":3.5,"sector_resources":45,"sector_industry":20,"sector_services":28,"sector_technology":7,"tax_rate":0.10,"treasury":20,"inflation":2.0,"trade_balance":8,"oil_producer":true,"opec_member":true,"opec_production":"normal","formosa_dependency":0.20,"debt_burden":0.25,"social_baseline":0.25,"oil_production_mbpd":10,"mil_ground":3,"mil_naval":0,"mil_tactical_air":3,"mil_strategic_missiles":0,"mil_air_defense":1,"prod_cost_ground":3,"prod_cost_naval":5,"prod_cost_tactical":4,"prod_cap_ground":1,"prod_cap_naval":0,"prod_cap_tactical":1,"maintenance_per_unit":0.028,"strategic_missile_growth":0,"mobilization_pool":0,"stability":7,"political_support":65,"dem_rep_split_dem":0,"dem_rep_split_rep":0,"war_tiredness":1,"nuclear_level":0,"nuclear_rd_progress":0.10,"ai_level":1,"ai_rd_progress":0.20,"at_war_with":[],"home_zones":["solaria_1","solaria_2"]},
      "choson":   {"parallel":"North Korea","regime_type":"autocracy","team_type":"solo","team_size_min":1,"team_size_max":1,"ai_default":true,"gdp":0.3,"gdp_growth_base":0.5,"sector_resources":20,"sector_industry":40,"sector_services":35,"sector_technology":5,"tax_rate":0.50,"treasury":1,"inflation":10.0,"trade_balance":-0.5,"oil_producer":false,"opec_member":false,"opec_production":"na","formosa_dependency":0.0,"debt_burden":0,"social_baseline":0.10,"oil_production_mbpd":0,"mil_ground":8,"mil_naval":0,"mil_tactical_air":1,"mil_strategic_missiles":2,"mil_air_defense":1,"prod_cost_ground":0.33,"prod_cost_naval":1,"prod_cost_tactical":0.67,"prod_cap_ground":2,"prod_cap_naval":0,"prod_cap_tactical":1,"maintenance_per_unit":0.001,"strategic_missile_growth":0,"mobilization_pool":2,"stability":4,"political_support":70,"dem_rep_split_dem":0,"dem_rep_split_rep":0,"war_tiredness":0,"nuclear_level":1,"nuclear_rd_progress":0.50,"ai_level":0,"ai_rd_progress":0.0,"at_war_with":[],"home_zones":["choson"]},
      "hanguk":   {"parallel":"South Korea","regime_type":"democracy","team_type":"solo","team_size_min":1,"team_size_max":1,"ai_default":true,"gdp":18,"gdp_growth_base":2.2,"sector_resources":3,"sector_industry":33,"sector_services":42,"sector_technology":22,"tax_rate":0.36,"treasury":8,"inflation":2.5,"trade_balance":3,"oil_producer":false,"opec_member":false,"opec_production":"na","formosa_dependency":0.40,"debt_burden":0.55,"social_baseline":0.25,"oil_production_mbpd":0,"mil_ground":5,"mil_naval":1,"mil_tactical_air":3,"mil_strategic_missiles":0,"mil_air_defense":2,"prod_cost_ground":2,"prod_cost_naval":4,"prod_cost_tactical":3,"prod_cap_ground":2,"prod_cap_naval":0,"prod_cap_tactical":1,"maintenance_per_unit":0.012,"strategic_missile_growth":0,"mobilization_pool":0,"stability":6,"political_support":35,"dem_rep_split_dem":0,"dem_rep_split_rep":0,"war_tiredness":0,"nuclear_level":0,"nuclear_rd_progress":0.00,"ai_level":2,"ai_rd_progress":0.50,"at_war_with":[],"home_zones":["hanguk"]},
      "caribe":   {"parallel":"Cuba + Venezuela","regime_type":"autocracy","team_type":"solo","team_size_min":1,"team_size_max":1,"ai_default":true,"gdp":2,"gdp_growth_base":-1.0,"sector_resources":50,"sector_industry":20,"sector_services":25,"sector_technology":5,"tax_rate":0.30,"treasury":1,"inflation":60.0,"trade_balance":0,"oil_producer":true,"opec_member":false,"opec_production":"na","formosa_dependency":0.0,"debt_burden":5,"social_baseline":0.20,"oil_production_mbpd":0.8,"mil_ground":3,"mil_naval":0,"mil_tactical_air":0,"mil_strategic_missiles":0,"mil_air_defense":0,"prod_cost_ground":2,"prod_cost_naval":4,"prod_cost_tactical":3,"prod_cap_ground":1,"prod_cap_naval":0,"prod_cap_tactical":0,"maintenance_per_unit":0.007,"strategic_missile_growth":0,"mobilization_pool":0,"stability":3,"political_support":45,"dem_rep_split_dem":0,"dem_rep_split_rep":0,"war_tiredness":0,"nuclear_level":0,"nuclear_rd_progress":0.0,"ai_level":0,"ai_rd_progress":0.0,"at_war_with":[],"home_zones":["caribe"]},
      "mirage":   {"parallel":"UAE","regime_type":"autocracy","team_type":"solo","team_size_min":1,"team_size_max":1,"ai_default":true,"gdp":5,"gdp_growth_base":4.0,"sector_resources":30,"sector_industry":15,"sector_services":45,"sector_technology":10,"tax_rate":0.15,"treasury":15,"inflation":2.0,"trade_balance":5,"oil_producer":true,"opec_member":true,"opec_production":"normal","formosa_dependency":0.15,"debt_burden":0,"social_baseline":0.20,"oil_production_mbpd":3.5,"mil_ground":2,"mil_naval":0,"mil_tactical_air":2,"mil_strategic_missiles":0,"mil_air_defense":1,"prod_cost_ground":3,"prod_cost_naval":5,"prod_cost_tactical":4,"prod_cap_ground":1,"prod_cap_naval":0,"prod_cap_tactical":1,"maintenance_per_unit":0.014,"strategic_missile_growth":0,"mobilization_pool":0,"stability":8,"political_support":70,"dem_rep_split_dem":0,"dem_rep_split_rep":0,"war_tiredness":1,"nuclear_level":0,"nuclear_rd_progress":0.0,"ai_level":1,"ai_rd_progress":0.30,"at_war_with":[],"home_zones":["mirage"]}
    }'::jsonb,

    -- default_relationships (PLACEHOLDER — populate from relationships.csv in follow-up)
    '{
      "_source": "2 SEED/C_MECHANICS/C4_DATA/relationships.csv",
      "_todo": "Convert relationships.csv rows to canonical {from_country: {to_country: {relationship, dynamic}}} JSONB shape",
      "_status": "placeholder"
    }'::jsonb,

    -- default_role_briefings (PLACEHOLDER — populate from roles.csv in follow-up)
    '{
      "_source": "2 SEED/C_MECHANICS/C4_DATA/roles.csv",
      "_todo": "Assemble per-role briefings + personas from roles.csv",
      "_status": "placeholder"
    }'::jsonb,

    -- formula_coefficients (PLACEHOLDER — live in Python engine, extract in follow-up)
    '{
      "_source": "app/engine/config/*.py (parameter review 15/15, 2026-04-02)",
      "_todo": "Extract sanctions_coefficient, tariff_coefficient, GDP/stability/oil formulas from engine code",
      "_status": "placeholder",
      "_locked": true
    }'::jsonb,

    -- organizations (PLACEHOLDER catalog; expand as needed)
    '{
      "UNSC": {"code": "UNSC", "name": "United Nations Security Council", "description": "Global security governance body.", "default_members": [], "enforcement_status": "none"},
      "EREB_UNION": {"code": "EREB_UNION", "name": "Ereb Union", "description": "Regional political+economic union (Europe parallel).", "default_members": [], "enforcement_status": "none"},
      "OPEC": {"code": "OPEC", "name": "Organization of Petroleum Exporting Countries", "description": "Oil producers cartel.", "default_members": [], "enforcement_status": "none"},
      "BRICS": {"code": "BRICS", "name": "BRICS bloc", "description": "Emerging-economies alignment.", "default_members": [], "enforcement_status": "none"},
      "NATO": {"code": "NATO", "name": "North Atlantic Treaty Organization", "description": "Collective defense alliance.", "default_members": [], "enforcement_status": "none"}
    }'::jsonb,

    -- allowed_round_counts
    ARRAY[6, 8]::INT[],

    -- allowed_oil_price_range
    '[50.0,150.0]'::numrange,

    -- allowed_phase_a_duration_range (seconds)
    '[300,1200]'::int4range,

    -- allowed_theaters
    ARRAY['eastern_ereb','mashriq']::TEXT[],

    'build-team'
);

-- ---------------------------------------------------------------------
-- 2. Insert default unit layout
-- ---------------------------------------------------------------------
INSERT INTO unit_layouts (code, name, template_id, description, unit_count, created_by) VALUES (
    'template_v1_0_default',
    'Template v1.0 Default Deployment',
    (SELECT id FROM sim_templates WHERE code = 'ttt_v1_0'),
    'Canonical default deployment from 2 SEED/C_MECHANICS/C4_DATA/units.csv v1.0 (345 units across 20 countries).',
    345,
    'build-team'
);

-- ---------------------------------------------------------------------
-- 3. Link template to default layout
-- ---------------------------------------------------------------------
UPDATE sim_templates
SET default_unit_layout_id = (SELECT id FROM unit_layouts WHERE code = 'template_v1_0_default')
WHERE code = 'ttt_v1_0';

-- ---------------------------------------------------------------------
-- 4. Insert 345 layout_units (from units.csv)
-- ---------------------------------------------------------------------
-- Uses subquery for layout_id to keep each row self-contained.
-- Source: 2 SEED/C_MECHANICS/C4_DATA/units.csv (verified 2026-04-05)

WITH layout AS (SELECT id FROM unit_layouts WHERE code = 'template_v1_0_default')
INSERT INTO layout_units (layout_id, unit_code, country_code, unit_type, global_row, global_col, theater, theater_row, theater_col, embarked_on, status, notes)
SELECT layout.id, v.* FROM layout, (VALUES
  ('col_g_01', 'columbia', 'ground', NULL::int, NULL::int, NULL::text, NULL::int, NULL::int, 'col_n_06', 'embarked', 'CONUS central - Ft Campbell/Pentagon'),
  ('col_g_02', 'columbia', 'ground', NULL, NULL, NULL, NULL, NULL, 'col_n_03', 'embarked', 'CONUS east coast - Ft Liberty'),
  ('col_g_03', 'columbia', 'ground', NULL, NULL, NULL, NULL, NULL, 'col_n_03', 'embarked', 'CONUS south central - Ft Hood/Cavazos'),
  ('col_g_04', 'columbia', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'CONUS southeast - Ft Stewart'),
  ('col_g_05', 'columbia', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Pacific NW - JBLM I Corps'),
  ('col_g_06', 'columbia', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'California - MCB Pendleton'),
  ('col_g_07', 'columbia', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'CONUS south - Ft Bliss'),
  ('col_g_08', 'columbia', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'CONUS central reserve brigade forward'),
  ('col_g_09', 'columbia', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Poland V Corps HQ forward'),
  ('col_g_10', 'columbia', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Poland ABCT rotational'),
  ('col_g_11', 'columbia', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Poland CAB rotational'),
  ('col_g_12', 'columbia', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Germany Grafenwoehr/Ramstein'),
  ('col_g_13', 'columbia', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Germany 2CR Vilseck'),
  ('col_g_14', 'columbia', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Israel coordination element/THAAD crew'),
  ('col_g_15', 'columbia', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'USFK Camp Humphreys 2ID'),
  ('col_g_16', 'columbia', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'USFK 2nd ABCT rotational'),
  ('col_g_17', 'columbia', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Okinawa III MEF'),
  ('col_g_18', 'columbia', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Formosa advise-assist element'),
  ('col_g_19', 'columbia', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'SOUTHCOM JTF-Bravo presence'),
  ('col_g_20', 'columbia', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Gulf basing Saudi/Kuwait Op Epic Fury logistics'),
  ('col_g_21', 'columbia', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Marines ARG Red Sea - Iran crisis'),
  ('col_g_22', 'columbia', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'UAE basing small footprint'),
  ('col_a_01', 'columbia', 'tactical_air', NULL, NULL, NULL, NULL, NULL, 'col_n_r1', 'embarked', 'CONUS central air'),
  ('col_a_02', 'columbia', 'tactical_air', NULL, NULL, NULL, NULL, NULL, 'col_n_10', 'embarked', 'CONUS east coast air'),
  ('col_a_03', 'columbia', 'tactical_air', NULL, NULL, NULL, NULL, NULL, 'col_n_05', 'embarked', 'CONUS south central air'),
  ('col_a_04', 'columbia', 'tactical_air', NULL, NULL, NULL, NULL, NULL, 'col_n_04', 'embarked', 'Alaska/PACAF air defense'),
  ('col_a_05', 'columbia', 'tactical_air', 8, 11, 'mashriq', 10, 5, NULL, 'active', 'Poland F-16/F-35 rotations'),
  ('col_a_06', 'columbia', 'tactical_air', 8, 11, 'mashriq', 10, 4, NULL, 'active', 'Ramstein/Spangdahlem'),
  ('col_a_07', 'columbia', 'tactical_air', 8, 11, 'mashriq', 10, 5, NULL, 'active', 'Prince Sultan Al Udeid'),
  ('col_a_08', 'columbia', 'tactical_air', 7, 11, 'mashriq', 4, 1, NULL, 'active', 'Al-Dhafra UAE'),
  ('col_a_09', 'columbia', 'tactical_air', 7, 11, 'mashriq', 4, 1, NULL, 'active', 'Israel joint air coordination'),
  ('col_a_10', 'columbia', 'tactical_air', NULL, NULL, NULL, NULL, NULL, 'col_n_03', 'embarked', 'Kadena Okinawa'),
  ('col_a_11', 'columbia', 'tactical_air', NULL, NULL, NULL, NULL, NULL, 'col_n_07', 'embarked', 'Osan/Kunsan'),
  ('col_a_12', 'columbia', 'tactical_air', NULL, NULL, NULL, NULL, NULL, 'col_n_08', 'embarked', 'Formosa air advisory'),
  ('col_a_13', 'columbia', 'tactical_air', NULL, NULL, NULL, NULL, NULL, 'col_n_09', 'embarked', 'CVW embarked on CVN CENTCOM'),
  ('col_a_r1', 'columbia', 'tactical_air', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'ANG/AFRC surge reserve'),
  ('col_a_r2', 'columbia', 'tactical_air', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'CONUS training/surge reserve'),
  ('col_m_01', 'columbia', 'strategic_missile', 3, 3, NULL, NULL, NULL, NULL, 'active', 'ICBM silo Minuteman III Warren/Malmstrom'),
  ('col_m_02', 'columbia', 'strategic_missile', 3, 3, NULL, NULL, NULL, NULL, 'active', 'ICBM silo Minuteman III Minot field'),
  ('col_m_03', 'columbia', 'strategic_missile', 5, 5, NULL, NULL, NULL, NULL, 'active', 'Atlantic SSBN patrol'),
  ('col_m_04', 'columbia', 'strategic_missile', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Pacific strategic strike'),
  ('col_m_05', 'columbia', 'strategic_missile', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Southeast B-2/B-21 strategic'),
  ('col_m_06', 'columbia', 'strategic_missile', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Pacific SSBN bastion'),
  ('col_m_07', 'columbia', 'strategic_missile', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Pacific SSBN Bangor'),
  ('col_m_08', 'columbia', 'strategic_missile', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Texas B-52 strategic'),
  ('col_m_09', 'columbia', 'strategic_missile', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'B61 tactical nuclear forward Europe'),
  ('col_m_10', 'columbia', 'strategic_missile', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Pacific theater deterrent'),
  ('col_m_11', 'columbia', 'strategic_missile', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Pacific theater second'),
  ('col_m_12', 'columbia', 'strategic_missile', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Gulf theater strategic strike'),
  ('col_d_01', 'columbia', 'air_defense', 5, 4, NULL, NULL, NULL, NULL, 'active', 'CONUS central Patriot NCR'),
  ('col_d_02', 'columbia', 'air_defense', 4, 2, NULL, NULL, NULL, NULL, 'active', 'CONUS south Patriot'),
  ('col_d_03', 'columbia', 'air_defense', 7, 4, NULL, NULL, NULL, NULL, 'active', 'Pacific NW GBI Ft Greely homeland'),
  ('col_d_04', 'columbia', 'air_defense', 8, 11, 'mashriq', 10, 4, NULL, 'active', 'Patriot Poland forward Europe'),
  ('col_d_05', 'columbia', 'air_defense', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'PAC-3/THAAD Pacific forward'),
  ('col_d_06', 'columbia', 'air_defense', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Patriot Gulf forward ME'),
  ('col_n_01', 'columbia', 'naval', 8, 4, NULL, NULL, NULL, NULL, 'active', 'CVN CSG Arabian Sea CENTCOM Lincoln'),
  ('col_n_02', 'columbia', 'naval', 9, 6, NULL, NULL, NULL, NULL, 'active', 'CVN CSG Arabian Sea CENTCOM Ford'),
  ('col_n_03', 'columbia', 'naval', 10, 12, NULL, NULL, NULL, NULL, 'active', 'DDG/SSN CENTCOM escort'),
  ('col_n_04', 'columbia', 'naval', 9, 12, NULL, NULL, NULL, NULL, 'active', 'ARG Tripoli+Boxer Red Sea amphib'),
  ('col_n_05', 'columbia', 'naval', 9, 13, NULL, NULL, NULL, NULL, 'active', 'DDG Red Sea strike support'),
  ('col_n_06', 'columbia', 'naval', 4, 5, NULL, NULL, NULL, NULL, 'active', '7th Fleet WestPac Formosa patrol'),
  ('col_n_07', 'columbia', 'naval', 9, 18, NULL, NULL, NULL, NULL, 'active', '7th Fleet WestPac CSG'),
  ('col_n_08', 'columbia', 'naval', 8, 18, NULL, NULL, NULL, NULL, 'active', 'Caribbean SOUTHCOM'),
  ('col_n_09', 'columbia', 'naval', 5, 20, NULL, NULL, NULL, NULL, 'active', 'Atlantic Norfolk home'),
  ('col_n_10', 'columbia', 'naval', 8, 12, 'mashriq', 10, 7, NULL, 'active', '6th Fleet Med'),
  ('col_n_r1', 'columbia', 'naval', 8, 12, 'mashriq', 7, 4, NULL, 'active', 'Naval reserve refit'),
  ('cat_g_01', 'cathay', 'ground', 6, 16, NULL, NULL, NULL, NULL, 'active', 'ETC Taiwan-facing Nanjing MR'),
  ('cat_g_02', 'cathay', 'ground', 7, 16, NULL, NULL, NULL, NULL, 'active', 'ETC Taiwan-facing Nanjing MR'),
  ('cat_g_03', 'cathay', 'ground', 5, 17, NULL, NULL, NULL, NULL, 'active', 'ETC Taiwan-facing Nanjing MR'),
  ('cat_g_04', 'cathay', 'ground', 5, 15, NULL, NULL, NULL, NULL, 'active', 'ETC Taiwan-facing Nanjing MR'),
  ('cat_g_05', 'cathay', 'ground', 6, 15, NULL, NULL, NULL, NULL, 'active', 'ETC South Cathay coastal'),
  ('cat_g_06', 'cathay', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'ETC South Cathay coastal'),
  ('cat_g_07', 'cathay', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'WTC India/Tibet border'),
  ('cat_g_08', 'cathay', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'WTC India/Tibet border'),
  ('cat_g_09', 'cathay', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'WTC India/Tibet border'),
  ('cat_g_10', 'cathay', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'WTC Xinjiang northwest'),
  ('cat_g_11', 'cathay', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'WTC Xinjiang northwest'),
  ('cat_g_12', 'cathay', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'NTC Choson/Russia border'),
  ('cat_g_13', 'cathay', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'NTC Choson/Russia border'),
  ('cat_g_14', 'cathay', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'NTC Choson/Russia border'),
  ('cat_g_15', 'cathay', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'NTC forward Choson border QRF'),
  ('cat_g_16', 'cathay', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'STC South China Sea staging'),
  ('cat_g_17', 'cathay', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'STC South China Sea staging'),
  ('cat_g_18', 'cathay', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'STC SCS staging'),
  ('cat_g_19', 'cathay', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'CTC Beijing central'),
  ('cat_g_20', 'cathay', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'CTC Beijing central'),
  ('cat_g_21', 'cathay', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'CTC Beijing central'),
  ('cat_g_r1', 'cathay', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'CTC strategic reserve'),
  ('cat_g_r2', 'cathay', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'CTC strategic reserve'),
  ('cat_g_r3', 'cathay', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'WTC strategic reserve'),
  ('cat_g_r4', 'cathay', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Airborne strategic reserve'),
  ('cat_a_01', 'cathay', 'tactical_air', NULL, NULL, NULL, NULL, NULL, 'cat_n_02', 'embarked', 'ETC aviation Taiwan strike'),
  ('cat_a_02', 'cathay', 'tactical_air', NULL, NULL, NULL, NULL, NULL, 'cat_n_06', 'embarked', 'ETC aviation Taiwan strike'),
  ('cat_a_03', 'cathay', 'tactical_air', NULL, NULL, NULL, NULL, NULL, 'cat_n_01', 'embarked', 'ETC aviation Taiwan strike'),
  ('cat_a_04', 'cathay', 'tactical_air', NULL, NULL, NULL, NULL, NULL, 'cat_n_01', 'embarked', 'ETC southern air'),
  ('cat_a_05', 'cathay', 'tactical_air', 7, 16, NULL, NULL, NULL, NULL, 'active', 'WTC western aviation'),
  ('cat_a_06', 'cathay', 'tactical_air', 6, 16, NULL, NULL, NULL, NULL, 'active', 'STC SCS air'),
  ('cat_a_07', 'cathay', 'tactical_air', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'STC SCS air'),
  ('cat_a_08', 'cathay', 'tactical_air', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'NTC northern air'),
  ('cat_a_09', 'cathay', 'tactical_air', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'CTC central air'),
  ('cat_a_10', 'cathay', 'tactical_air', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'WTC Xinjiang air'),
  ('cat_a_11', 'cathay', 'tactical_air', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Carrier air wing Shandong/Fujian'),
  ('cat_a_r1', 'cathay', 'tactical_air', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Hardened air reserve'),
  ('cat_m_01', 'cathay', 'strategic_missile', 6, 15, NULL, NULL, NULL, NULL, 'active', 'DF-21/DF-26 carrier killer coast'),
  ('cat_m_02', 'cathay', 'strategic_missile', 6, 15, NULL, NULL, NULL, NULL, 'active', 'SSBN SCS bastion'),
  ('cat_m_03', 'cathay', 'strategic_missile', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'DF-41 mobile interior'),
  ('cat_m_r1', 'cathay', 'strategic_missile', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Silo ICBM reserve'),
  ('cat_d_01', 'cathay', 'air_defense', 6, 15, NULL, NULL, NULL, NULL, 'active', 'HQ-9 ETC coastal'),
  ('cat_d_02', 'cathay', 'air_defense', 5, 17, NULL, NULL, NULL, NULL, 'active', 'HQ-9 Beijing'),
  ('cat_d_03', 'cathay', 'air_defense', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'HQ-9 western'),
  ('cat_n_01', 'cathay', 'naval', 7, 17, NULL, NULL, NULL, NULL, 'active', 'East Sea Fleet Formosa north'),
  ('cat_n_02', 'cathay', 'naval', 6, 17, NULL, NULL, NULL, NULL, 'active', 'East Sea Fleet carrier'),
  ('cat_n_03', 'cathay', 'naval', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'South Sea Fleet SCS north'),
  ('cat_n_04', 'cathay', 'naval', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'South Sea Fleet Hainan home'),
  ('cat_n_05', 'cathay', 'naval', 7, 17, NULL, NULL, NULL, NULL, 'active', 'North Sea Fleet Qingdao'),
  ('cat_n_06', 'cathay', 'naval', 8, 16, NULL, NULL, NULL, NULL, 'active', 'Distant water Indian Ocean'),
  ('cat_n_r1', 'cathay', 'naval', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Fleet reserve refit'),
  ('sar_g_01', 'sarmatia', 'ground', 4, 11, 'eastern_ereb', 4, 5, NULL, 'active', 'Pokrovsk/Donetsk axis'),
  ('sar_g_02', 'sarmatia', 'ground', 4, 11, 'eastern_ereb', 5, 6, NULL, 'active', 'Pokrovsk/Donetsk axis'),
  ('sar_g_03', 'sarmatia', 'ground', 4, 11, 'eastern_ereb', 5, 7, NULL, 'active', 'Pokrovsk/Donetsk axis'),
  ('sar_g_04', 'sarmatia', 'ground', 4, 11, 'eastern_ereb', 6, 7, NULL, 'active', 'Luhansk/Lyman occupation'),
  ('sar_g_05', 'sarmatia', 'ground', 4, 11, 'eastern_ereb', 7, 8, NULL, 'active', 'Luhansk/Lyman occupation'),
  ('sar_g_06', 'sarmatia', 'ground', 4, 11, 'eastern_ereb', 7, 7, NULL, 'active', 'Bakhmut/Chasiv Yar'),
  ('sar_g_07', 'sarmatia', 'ground', 4, 11, 'eastern_ereb', 6, 7, NULL, 'active', 'Zaporizhzhia front west'),
  ('sar_g_08', 'sarmatia', 'ground', 4, 11, 'eastern_ereb', 7, 6, NULL, 'active', 'Zaporizhzhia front east'),
  ('sar_g_09', 'sarmatia', 'ground', 4, 11, 'eastern_ereb', 8, 5, NULL, 'active', 'Kherson occupation lower Dnipro'),
  ('sar_g_10', 'sarmatia', 'ground', 4, 11, 'eastern_ereb', 8, 5, NULL, 'active', 'Crimea/occupied south'),
  ('sar_g_11', 'sarmatia', 'ground', 4, 11, 'eastern_ereb', 5, 6, NULL, 'active', 'Northern Grouping Kursk'),
  ('sar_g_12', 'sarmatia', 'ground', 4, 11, 'eastern_ereb', 7, 7, NULL, 'active', 'Northern Grouping Belgorod'),
  ('sar_g_13', 'sarmatia', 'ground', 4, 12, 'eastern_ereb', 6, 8, NULL, 'active', 'Northern Grouping Voronezh'),
  ('sar_g_14', 'sarmatia', 'ground', 4, 16, NULL, NULL, NULL, NULL, 'active', 'Kaliningrad exclave defense'),
  ('sar_g_15', 'sarmatia', 'ground', 2, 11, NULL, NULL, NULL, NULL, 'active', 'Moscow VO garrison'),
  ('sar_g_16', 'sarmatia', 'ground', 4, 13, NULL, NULL, NULL, NULL, 'active', 'Arctic/Kola'),
  ('sar_g_17', 'sarmatia', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Far East/Cathay border'),
  ('sar_g_r1', 'sarmatia', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'VDV strategic reserve'),
  ('sar_a_01', 'sarmatia', 'tactical_air', 4, 11, 'eastern_ereb', 5, 6, NULL, 'active', 'Front-area Russia-side airbase glide bombs'),
  ('sar_a_02', 'sarmatia', 'tactical_air', 4, 11, 'eastern_ereb', 5, 7, NULL, 'active', 'Front-area Russia-side airbase glide bombs'),
  ('sar_a_03', 'sarmatia', 'tactical_air', 4, 11, 'eastern_ereb', 4, 5, NULL, 'active', 'Front-area Russia-side airbase drones'),
  ('sar_a_04', 'sarmatia', 'tactical_air', 4, 11, 'eastern_ereb', 7, 6, NULL, 'active', 'Front-area Russia-side airbase'),
  ('sar_a_05', 'sarmatia', 'tactical_air', 4, 11, 'eastern_ereb', 7, 7, NULL, 'active', 'Homeland air defense Moscow VO'),
  ('sar_a_06', 'sarmatia', 'tactical_air', 4, 11, 'eastern_ereb', 9, 5, NULL, 'active', 'Homeland air defense Moscow VO'),
  ('sar_a_07', 'sarmatia', 'tactical_air', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Kaliningrad strike aviation'),
  ('sar_a_r1', 'sarmatia', 'tactical_air', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Strategic aviation reserve'),
  ('sar_m_01', 'sarmatia', 'strategic_missile', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Strategic ICBM silo Moscow VO'),
  ('sar_m_02', 'sarmatia', 'strategic_missile', 2, 16, NULL, NULL, NULL, NULL, 'active', 'Strategic ICBM silo Moscow VO'),
  ('sar_m_03', 'sarmatia', 'strategic_missile', 2, 12, NULL, NULL, NULL, NULL, 'active', 'Strategic ICBM silo Moscow VO'),
  ('sar_m_04', 'sarmatia', 'strategic_missile', 2, 12, NULL, NULL, NULL, NULL, 'active', 'Strategic ICBM silo Moscow VO'),
  ('sar_m_05', 'sarmatia', 'strategic_missile', 2, 16, NULL, NULL, NULL, NULL, 'active', 'Mobile launcher south central'),
  ('sar_m_06', 'sarmatia', 'strategic_missile', 2, 12, NULL, NULL, NULL, NULL, 'active', 'Mobile launcher Pacific'),
  ('sar_m_07', 'sarmatia', 'strategic_missile', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'SSBN Northern Fleet bastion'),
  ('sar_m_08', 'sarmatia', 'strategic_missile', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Iskander front-line (occupied zone)'),
  ('sar_m_09', 'sarmatia', 'strategic_missile', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Iskander front-line (occupied zone)'),
  ('sar_m_10', 'sarmatia', 'strategic_missile', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Iskander front-line (occupied zone)'),
  ('sar_m_11', 'sarmatia', 'strategic_missile', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Kaliningrad Iskander'),
  ('sar_m_r1', 'sarmatia', 'strategic_missile', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Strategic missile reserve'),
  ('sar_d_01', 'sarmatia', 'air_defense', 3, 12, 'eastern_ereb', 1, 5, NULL, 'active', 'S-400 Moscow central'),
  ('sar_d_02', 'sarmatia', 'air_defense', 3, 12, 'eastern_ereb', 4, 9, NULL, 'active', 'S-400 Crimea/occupied zone'),
  ('sar_d_03', 'sarmatia', 'air_defense', 3, 16, NULL, NULL, NULL, NULL, 'active', 'S-400 Kaliningrad'),
  ('sar_n_01', 'sarmatia', 'naval', 5, 12, 'eastern_ereb', 8, 4, NULL, 'active', 'Black Sea Fleet'),
  ('sar_n_02', 'sarmatia', 'naval', 2, 17, NULL, NULL, NULL, NULL, 'active', 'Northern Fleet Arctic'),
  ('rut_g_01', 'ruthenia', 'ground', 4, 11, 'eastern_ereb', 6, 6, NULL, 'active', 'Die Hard core - Fortress Belt Kramatorsk'),
  ('rut_g_02', 'ruthenia', 'ground', 4, 11, 'eastern_ereb', 6, 6, NULL, 'active', 'Die Hard core - Fortress Belt Sloviansk'),
  ('rut_g_05', 'ruthenia', 'ground', 4, 11, 'eastern_ereb', 5, 5, NULL, 'active', 'Fortress Belt northern wing Lyman'),
  ('rut_g_06', 'ruthenia', 'ground', 4, 11, 'eastern_ereb', 4, 4, NULL, 'active', 'Fortress Belt Chasiv Yar'),
  ('rut_g_07', 'ruthenia', 'ground', 4, 11, 'eastern_ereb', 5, 5, NULL, 'active', 'Kharkiv-Kupyansk northern axis'),
  ('rut_g_08', 'ruthenia', 'ground', 4, 11, 'eastern_ereb', 7, 5, NULL, 'active', 'Zaporizhzhia counter-offensive'),
  ('rut_g_09', 'ruthenia', 'ground', 4, 11, 'eastern_ereb', 6, 5, NULL, 'active', 'Sumy border north'),
  ('rut_g_10', 'ruthenia', 'ground', 4, 11, 'eastern_ereb', 3, 3, NULL, 'active', 'Strategic reserve Dnipro rear'),
  ('rut_a_01', 'ruthenia', 'tactical_air', 4, 11, 'eastern_ereb', 6, 6, NULL, 'active', 'Die Hard CAS close air support'),
  ('rut_a_02', 'ruthenia', 'tactical_air', 4, 11, 'eastern_ereb', 5, 5, NULL, 'active', 'Western dispersal bases'),
  ('rut_a_03', 'ruthenia', 'tactical_air', 4, 11, 'eastern_ereb', 7, 5, NULL, 'active', 'Central Kyiv area'),
  ('rut_d_01', 'ruthenia', 'air_defense', 4, 11, 'eastern_ereb', 6, 2, NULL, 'active', 'Patriot/NASAMS Die Hard protection'),
  ('per_g_01', 'persia', 'ground', 6, 12, 'mashriq', 2, 4, NULL, 'active', 'Kermanshah Iraq-facing IRGC'),
  ('per_g_02', 'persia', 'ground', 6, 12, 'mashriq', 3, 5, NULL, 'active', 'Hamadan western defense'),
  ('per_g_03', 'persia', 'ground', 7, 13, 'mashriq', 5, 7, NULL, 'active', 'Tehran central'),
  ('per_g_04', 'persia', 'ground', 7, 13, 'mashriq', 4, 5, NULL, 'active', 'Nuclear sites central defense'),
  ('per_g_05', 'persia', 'ground', 7, 13, 'mashriq', 6, 8, NULL, 'active', 'Central-south depth'),
  ('per_g_06', 'persia', 'ground', 8, 13, 'mashriq', 8, 6, NULL, 'active', 'Gulf coast Bushehr'),
  ('per_g_07', 'persia', 'ground', 8, 13, 'mashriq', 9, 9, NULL, 'active', 'Hormuz tip Bandar Abbas'),
  ('per_g_r1', 'persia', 'ground', 8, 13, 'mashriq', 7, 8, NULL, 'active', 'Hardened reserves dispersed'),
  ('per_a_01', 'persia', 'tactical_air', 8, 13, 'mashriq', 8, 6, NULL, 'active', 'Western dispersal'),
  ('per_a_02', 'persia', 'tactical_air', 8, 13, 'mashriq', 8, 6, NULL, 'active', 'Central Isfahan'),
  ('per_a_03', 'persia', 'tactical_air', 6, 12, 'mashriq', 2, 4, NULL, 'active', 'Central Shiraz'),
  ('per_a_04', 'persia', 'tactical_air', 6, 12, 'mashriq', 3, 5, NULL, 'active', 'Central-south dispersal'),
  ('per_a_05', 'persia', 'tactical_air', 8, 13, 'mashriq', 9, 9, NULL, 'active', 'Eastern dispersal'),
  ('per_a_r1', 'persia', 'tactical_air', 8, 13, 'mashriq', 8, 6, NULL, 'active', 'Hardened aviation reserve'),
  ('per_d_01', 'persia', 'air_defense', 8, 13, 'mashriq', 7, 7, NULL, 'active', 'S-300/S-400 nuclear sites central'),
  ('gal_g_01', 'gallia', 'ground', 5, 10, NULL, NULL, NULL, NULL, 'active', 'Metropolitan France west'),
  ('gal_g_02', 'gallia', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Metropolitan France west'),
  ('gal_g_03', 'gallia', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Metropolitan France east'),
  ('gal_g_04', 'gallia', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Romania NATO eFP'),
  ('gal_g_05', 'gallia', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Djibouti overseas'),
  ('gal_g_r1', 'gallia', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Metropolitan reserve'),
  ('gal_a_01', 'gallia', 'tactical_air', NULL, NULL, NULL, NULL, NULL, 'gal_n_01', 'embarked', 'Rafale Saint-Dizier'),
  ('gal_a_02', 'gallia', 'tactical_air', 5, 10, NULL, NULL, NULL, NULL, 'active', 'Rafale Mont-de-Marsan'),
  ('gal_a_03', 'gallia', 'tactical_air', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Rafale M on Charles de Gaulle'),
  ('gal_a_04', 'gallia', 'tactical_air', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'UAE deployment'),
  ('gal_m_01', 'gallia', 'strategic_missile', 5, 9, NULL, NULL, NULL, NULL, 'active', 'SSBN Le Triomphant class'),
  ('gal_m_r1', 'gallia', 'strategic_missile', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'ASMPA air-launched reserve'),
  ('gal_d_01', 'gallia', 'air_defense', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'SAMP/T metropolitan'),
  ('gal_n_01', 'gallia', 'naval', 6, 9, NULL, NULL, NULL, NULL, 'active', 'Charles de Gaulle CSG Eastern Med'),
  ('teu_g_01', 'teutonia', 'ground', 4, 10, NULL, NULL, NULL, NULL, 'active', 'Bundeswehr north'),
  ('teu_g_02', 'teutonia', 'ground', 4, 10, NULL, NULL, NULL, NULL, 'active', 'Bundeswehr north'),
  ('teu_g_03', 'teutonia', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Bundeswehr south'),
  ('teu_g_04', 'teutonia', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', '45th Brigade Lithuania via Poland'),
  ('teu_g_05', 'teutonia', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'eFP rotations Baltic'),
  ('teu_g_r1', 'teutonia', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Operational reserve'),
  ('teu_a_01', 'teutonia', 'tactical_air', 4, 10, NULL, NULL, NULL, NULL, 'active', 'Eurofighter north'),
  ('teu_a_02', 'teutonia', 'tactical_air', 4, 10, NULL, NULL, NULL, NULL, 'active', 'Eurofighter south'),
  ('teu_a_03', 'teutonia', 'tactical_air', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Baltic air policing'),
  ('teu_d_01', 'teutonia', 'air_defense', 4, 9, NULL, NULL, NULL, NULL, 'active', 'Patriot Germany central'),
  ('fre_g_01', 'freeland', 'ground', 2, 10, NULL, NULL, NULL, NULL, 'active', 'Eastern border defense'),
  ('fre_g_02', 'freeland', 'ground', 2, 10, NULL, NULL, NULL, NULL, 'active', 'Eastern border defense'),
  ('fre_g_03', 'freeland', 'ground', 2, 10, NULL, NULL, NULL, NULL, 'active', 'Eastern border defense'),
  ('fre_g_04', 'freeland', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Central homeland Warsaw'),
  ('fre_g_r1', 'freeland', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Territorial reserve'),
  ('fre_a_01', 'freeland', 'tactical_air', 2, 10, NULL, NULL, NULL, NULL, 'active', 'F-35 eastern bases'),
  ('fre_a_02', 'freeland', 'tactical_air', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'FA-50 southern bases'),
  ('fre_d_01', 'freeland', 'air_defense', 3, 10, NULL, NULL, NULL, NULL, 'active', 'Patriot Warsaw/east'),
  ('pon_g_01', 'ponte', 'ground', 7, 9, NULL, NULL, NULL, NULL, 'active', 'Metropolitan Italy'),
  ('pon_g_02', 'ponte', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Metropolitan Italy'),
  ('pon_g_03', 'ponte', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Lebanon UNIFIL rotation'),
  ('pon_g_r1', 'ponte', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Alpini reserve'),
  ('pon_a_01', 'ponte', 'tactical_air', 7, 9, NULL, NULL, NULL, NULL, 'active', 'Eurofighter Italy'),
  ('pon_a_02', 'ponte', 'tactical_air', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'F-35 Italy'),
  ('alb_g_01', 'albion', 'ground', 4, 7, NULL, NULL, NULL, NULL, 'active', 'UK home brigades'),
  ('alb_g_02', 'albion', 'ground', NULL, NULL, NULL, NULL, NULL, 'alb_n_02', 'embarked', 'UK home brigades'),
  ('alb_g_03', 'albion', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Estonia eFP via Germany staging'),
  ('alb_g_04', 'albion', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Cyprus overseas'),
  ('alb_a_01', 'albion', 'tactical_air', 3, 8, NULL, NULL, NULL, NULL, 'active', 'RAF Typhoon home'),
  ('alb_a_02', 'albion', 'tactical_air', NULL, NULL, NULL, NULL, NULL, 'alb_n_02', 'embarked', 'RAF F-35B home'),
  ('alb_a_03', 'albion', 'tactical_air', NULL, NULL, NULL, NULL, NULL, 'alb_n_01', 'embarked', 'F-35B on Prince of Wales'),
  ('alb_m_01', 'albion', 'strategic_missile', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Trident SSBN CASD'),
  ('alb_m_02', 'albion', 'strategic_missile', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Conventional strike reserve'),
  ('alb_d_01', 'albion', 'air_defense', 3, 8, NULL, NULL, NULL, NULL, 'active', 'Sky Sabre UK'),
  ('alb_n_01', 'albion', 'naval', 7, 10, NULL, NULL, NULL, NULL, 'active', 'HMS Prince of Wales CSG Eastern Med'),
  ('alb_n_02', 'albion', 'naval', 9, 11, NULL, NULL, NULL, NULL, 'active', 'Atlantic/Gulf deployer'),
  ('bha_g_01', 'bharata', 'ground', 8, 14, NULL, NULL, NULL, NULL, 'active', 'LAC China border'),
  ('bha_g_02', 'bharata', 'ground', 7, 14, NULL, NULL, NULL, NULL, 'active', 'LAC China border'),
  ('bha_g_03', 'bharata', 'ground', 7, 14, NULL, NULL, NULL, NULL, 'active', 'LAC China border'),
  ('bha_g_04', 'bharata', 'ground', 7, 15, NULL, NULL, NULL, NULL, 'active', 'LAC China border'),
  ('bha_g_05', 'bharata', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Pakistan border western'),
  ('bha_g_06', 'bharata', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Pakistan border western'),
  ('bha_g_07', 'bharata', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Pakistan border western'),
  ('bha_g_08', 'bharata', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Pakistan border western'),
  ('bha_g_09', 'bharata', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Internal security northern'),
  ('bha_g_10', 'bharata', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Southern command'),
  ('bha_g_r1', 'bharata', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Strategic reserve'),
  ('bha_g_r2', 'bharata', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Strategic reserve'),
  ('bha_a_01', 'bharata', 'tactical_air', NULL, NULL, NULL, NULL, NULL, 'bha_n_01', 'embarked', 'Northern Su-30MKI'),
  ('bha_a_02', 'bharata', 'tactical_air', 8, 14, NULL, NULL, NULL, NULL, 'active', 'Northern Rafale'),
  ('bha_a_03', 'bharata', 'tactical_air', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Western Pakistan facing'),
  ('bha_a_04', 'bharata', 'tactical_air', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Central Tejas'),
  ('bha_d_01', 'bharata', 'air_defense', 7, 15, NULL, NULL, NULL, NULL, 'active', 'S-400 Delhi/Punjab'),
  ('bha_d_02', 'bharata', 'air_defense', 9, 15, NULL, NULL, NULL, NULL, 'active', 'Akash northern'),
  ('bha_n_01', 'bharata', 'naval', 9, 14, NULL, NULL, NULL, NULL, 'active', 'Arabian Sea fleet'),
  ('bha_n_02', 'bharata', 'naval', 10, 17, NULL, NULL, NULL, NULL, 'active', 'Bay of Bengal fleet'),
  ('lev_g_01', 'levantia', 'ground', 6, 10, NULL, NULL, NULL, NULL, 'active', 'Lebanon northern front'),
  ('lev_g_02', 'levantia', 'ground', 6, 10, NULL, NULL, NULL, NULL, 'active', 'Lebanon northern front'),
  ('lev_g_03', 'levantia', 'ground', 6, 10, NULL, NULL, NULL, NULL, 'active', 'Gaza southern front'),
  ('lev_g_04', 'levantia', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'West Bank'),
  ('lev_g_05', 'levantia', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Northern home defense'),
  ('lev_g_06', 'levantia', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Southern home Persia-facing'),
  ('lev_a_01', 'levantia', 'tactical_air', 6, 10, NULL, NULL, NULL, NULL, 'active', 'F-35I all committed'),
  ('lev_a_02', 'levantia', 'tactical_air', 6, 10, NULL, NULL, NULL, NULL, 'active', 'F-15I all committed'),
  ('lev_a_03', 'levantia', 'tactical_air', 6, 10, NULL, NULL, NULL, NULL, 'active', 'F-16I strike'),
  ('lev_a_04', 'levantia', 'tactical_air', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'UAV/drone wing'),
  ('lev_d_01', 'levantia', 'air_defense', 6, 10, NULL, NULL, NULL, NULL, 'active', 'Iron Dome northern'),
  ('lev_d_02', 'levantia', 'air_defense', 6, 10, NULL, NULL, NULL, NULL, 'active', 'David''s Sling central'),
  ('lev_d_03', 'levantia', 'air_defense', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Arrow southern'),
  ('for_g_01', 'formosa', 'ground', 7, 18, NULL, NULL, NULL, NULL, 'active', 'Western coast anti-invasion'),
  ('for_g_02', 'formosa', 'ground', 7, 18, NULL, NULL, NULL, NULL, 'active', 'Western coast anti-invasion'),
  ('for_g_03', 'formosa', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Northern defense'),
  ('for_g_04', 'formosa', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Outlying islands reserves'),
  ('for_a_01', 'formosa', 'tactical_air', 7, 18, NULL, NULL, NULL, NULL, 'active', 'F-16V western bases'),
  ('for_a_02', 'formosa', 'tactical_air', 7, 18, NULL, NULL, NULL, NULL, 'active', 'F-16V western bases'),
  ('for_a_03', 'formosa', 'tactical_air', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Eastern dispersal Hualien'),
  ('for_d_01', 'formosa', 'air_defense', 7, 18, NULL, NULL, NULL, NULL, 'active', 'Patriot PAC-3 northern'),
  ('for_d_02', 'formosa', 'air_defense', 7, 18, NULL, NULL, NULL, NULL, 'active', 'Tien Kung southern'),
  ('phr_g_01', 'phrygia', 'ground', 6, 11, 'mashriq', 2, 2, NULL, 'active', 'Syria occupation zone'),
  ('phr_g_02', 'phrygia', 'ground', 6, 11, 'mashriq', 1, 3, NULL, 'active', 'Syria occupation zone'),
  ('phr_g_03', 'phrygia', 'ground', 6, 11, 'mashriq', 2, 2, NULL, 'active', 'Iraq operations'),
  ('phr_g_04', 'phrygia', 'ground', 6, 11, 'mashriq', 2, 1, NULL, 'active', 'Eastern Anatolia'),
  ('phr_g_05', 'phrygia', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Western Anatolia'),
  ('phr_g_06', 'phrygia', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Naval infantry on TCG Anadolu'),
  ('phr_a_01', 'phrygia', 'tactical_air', 6, 11, 'mashriq', 1, 3, NULL, 'active', 'F-16 central'),
  ('phr_a_02', 'phrygia', 'tactical_air', 6, 11, 'mashriq', 2, 2, NULL, 'active', 'Bayraktar central'),
  ('phr_a_03', 'phrygia', 'tactical_air', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Eastern air'),
  ('phr_d_01', 'phrygia', 'air_defense', 6, 11, 'mashriq', 1, 1, NULL, 'active', 'S-400 Ankara'),
  ('phr_n_01', 'phrygia', 'naval', 7, 12, 'mashriq', 4, 2, NULL, 'active', 'TCG Anadolu LHD Eastern Med'),
  ('yam_g_01', 'yamato', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Southwestern Okinawa'),
  ('yam_g_02', 'yamato', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Kyushu central'),
  ('yam_g_03', 'yamato', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Northern Hokkaido'),
  ('yam_a_01', 'yamato', 'tactical_air', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'F-35 southwestern'),
  ('yam_a_02', 'yamato', 'tactical_air', NULL, NULL, NULL, NULL, NULL, 'yam_n_01', 'embarked', 'F-15J southwestern'),
  ('yam_a_03', 'yamato', 'tactical_air', 5, 19, NULL, NULL, NULL, NULL, 'active', 'Central/Northern air'),
  ('yam_d_01', 'yamato', 'air_defense', 5, 19, NULL, NULL, NULL, NULL, 'active', 'PAC-3 central Okinawa'),
  ('yam_d_02', 'yamato', 'air_defense', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Aegis Ashore northern'),
  ('yam_n_01', 'yamato', 'naval', 6, 19, NULL, NULL, NULL, NULL, 'active', 'Sasebo western fleet'),
  ('yam_n_02', 'yamato', 'naval', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Yokosuka eastern fleet'),
  ('sol_g_01', 'solaria', 'ground', 7, 11, 'mashriq', 5, 1, NULL, 'active', 'Yemen border southern'),
  ('sol_g_02', 'solaria', 'ground', 7, 11, 'mashriq', 7, 1, NULL, 'active', 'Northern/Central'),
  ('sol_g_03', 'solaria', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Eastern Province Gulf'),
  ('sol_a_01', 'solaria', 'tactical_air', 7, 11, 'mashriq', 6, 1, NULL, 'active', 'Eastern Iran-facing'),
  ('sol_a_02', 'solaria', 'tactical_air', 7, 11, 'mashriq', 6, 1, NULL, 'active', 'Southern Yemen'),
  ('sol_a_03', 'solaria', 'tactical_air', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Northern F-15/Typhoon'),
  ('sol_d_01', 'solaria', 'air_defense', 7, 11, 'mashriq', 7, 1, NULL, 'active', 'Patriot Eastern Province'),
  ('cho_g_01', 'choson', 'ground', 3, 18, NULL, NULL, NULL, NULL, 'active', 'DMZ forward artillery'),
  ('cho_g_02', 'choson', 'ground', 3, 18, NULL, NULL, NULL, NULL, 'active', 'DMZ forward artillery'),
  ('cho_g_03', 'choson', 'ground', 3, 18, NULL, NULL, NULL, NULL, 'active', 'DMZ forward artillery'),
  ('cho_g_04', 'choson', 'ground', 3, 12, 'eastern_ereb', 3, 4, NULL, 'active', 'DMZ forward artillery'),
  ('cho_g_05', 'choson', 'ground', 3, 12, 'eastern_ereb', 3, 5, NULL, 'active', 'DMZ forward artillery'),
  ('cho_g_06', 'choson', 'ground', 3, 12, 'eastern_ereb', 2, 3, NULL, 'active', 'Pyongyang garrison'),
  ('cho_g_07', 'choson', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Northeast border'),
  ('cho_g_r1', 'choson', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Strategic reserve'),
  ('cho_a_01', 'choson', 'tactical_air', 3, 18, NULL, NULL, NULL, NULL, 'active', 'Southern bases'),
  ('cho_m_01', 'choson', 'strategic_missile', 3, 18, NULL, NULL, NULL, NULL, 'active', 'Dispersed TEL Hwasong'),
  ('cho_d_01', 'choson', 'air_defense', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Pyongyang layered defense'),
  ('han_g_01', 'hanguk', 'ground', 4, 17, NULL, NULL, NULL, NULL, 'active', 'DMZ western-central'),
  ('han_g_02', 'hanguk', 'ground', 4, 17, NULL, NULL, NULL, NULL, 'active', 'DMZ western-central'),
  ('han_g_03', 'hanguk', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Eastern DMZ'),
  ('han_g_04', 'hanguk', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Capital defense'),
  ('han_g_05', 'hanguk', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Southern + reserves'),
  ('han_a_01', 'hanguk', 'tactical_air', 4, 17, NULL, NULL, NULL, NULL, 'active', 'Central F-35'),
  ('han_a_02', 'hanguk', 'tactical_air', 4, 17, NULL, NULL, NULL, NULL, 'active', 'Central F-15K'),
  ('han_a_03', 'hanguk', 'tactical_air', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Southern KF-21'),
  ('han_d_01', 'hanguk', 'air_defense', 4, 17, NULL, NULL, NULL, NULL, 'active', 'Northern Patriot'),
  ('han_d_02', 'hanguk', 'air_defense', 4, 17, NULL, NULL, NULL, NULL, 'active', 'THAAD central/southern'),
  ('han_n_01', 'hanguk', 'naval', 4, 18, NULL, NULL, NULL, NULL, 'active', 'Eastern fleet'),
  ('car_g_01', 'caribe', 'ground', 9, 5, NULL, NULL, NULL, NULL, 'active', 'Venezuela fragmented'),
  ('car_g_02', 'caribe', 'ground', 9, 5, NULL, NULL, NULL, NULL, 'active', 'Cuba'),
  ('car_g_r1', 'caribe', 'ground', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Residual reserve'),
  ('mir_g_01', 'mirage', 'ground', 8, 11, 'mashriq', 10, 3, NULL, 'active', 'Northern'),
  ('mir_g_02', 'mirage', 'ground', 8, 11, 'mashriq', 9, 3, NULL, 'active', 'Southern'),
  ('mir_a_01', 'mirage', 'tactical_air', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Al-Dhafra'),
  ('mir_a_02', 'mirage', 'tactical_air', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Al-Minhad'),
  ('mir_d_02', 'mirage', 'air_defense', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', 'Patriot Southern Houthi'),
  ('alb_d_02', 'albion', 'air_defense', 4, 7, NULL, NULL, NULL, NULL, 'active', NULL),
  ('cho_m_02', 'choson', 'strategic_missile', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', NULL),
  ('rut_g_11', 'ruthenia', 'ground', 4, 11, 'eastern_ereb', 4, 3, NULL, 'active', NULL),
  ('rut_g_12', 'ruthenia', 'ground', 4, 11, 'eastern_ereb', 6, 5, NULL, 'active', NULL),
  ('lev_m_01', 'levantia', 'strategic_missile', 6, 10, NULL, NULL, NULL, NULL, 'active', NULL),
  ('lev_m_02', 'levantia', 'strategic_missile', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', NULL),
  ('lev_m_03', 'levantia', 'strategic_missile', NULL, NULL, NULL, NULL, NULL, NULL, 'reserve', NULL),
  ('rut_g_13', 'ruthenia', 'ground', 3, 11, NULL, NULL, NULL, NULL, 'active', NULL)
) AS v(unit_code, country_code, unit_type, global_row, global_col, theater, theater_row, theater_col, embarked_on, status, notes);

-- ---------------------------------------------------------------------
-- Verification query (run manually after seed)
-- ---------------------------------------------------------------------
-- SELECT COUNT(*) FROM layout_units
--   WHERE layout_id = (SELECT id FROM unit_layouts WHERE code = 'template_v1_0_default');
-- Expected: 345
--
-- SELECT country_code, COUNT(*)
--   FROM layout_units
--   WHERE layout_id = (SELECT id FROM unit_layouts WHERE code = 'template_v1_0_default')
--   GROUP BY country_code ORDER BY country_code;
-- =====================================================================
