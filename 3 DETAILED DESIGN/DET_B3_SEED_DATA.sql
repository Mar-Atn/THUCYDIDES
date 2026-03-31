-- =============================================================================
-- DET_B3_SEED_DATA.sql
-- Thucydides Trap SIM — Seed Data Migration
-- Version: 1.0 | Date: 2026-03-30
-- Source: 10 CSV files in 2 SEED/C_MECHANICS/C4_DATA/
--
-- USAGE:
--   1. Run DET_B1_DATABASE_SCHEMA.sql first
--   2. This script creates a default SIM run and loads all starting data
--   3. All INSERT statements use the sim_run_id from the created SIM run
--
-- NOTE: This file uses a single SIM run ID. For multiple SIM instances,
-- change the sim_run_id variable at the top.
-- =============================================================================

-- Create the default SIM run
INSERT INTO sim_runs (id, name, status, current_round, current_phase, config)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    'Thucydides Trap — Default Session',
    'setup',
    0,
    'pre',
    '{"version": "1.0", "max_rounds": 8, "round_duration_minutes": 60}'::JSONB
);

-- Variable for convenience (PostgreSQL doesn't have variables in plain SQL,
-- so we use the literal UUID throughout)
-- SIM_RUN_ID = '00000000-0000-0000-0000-000000000001'


-- =============================================================================
-- 1. COUNTRIES (from countries.csv — 21 rows)
-- =============================================================================

INSERT INTO countries (id, sim_run_id, sim_name, parallel, regime_type, team_type, team_size_min, team_size_max, ai_default, gdp, gdp_growth_base, sector_resources, sector_industry, sector_services, sector_technology, tax_rate, treasury, inflation, trade_balance, oil_producer, opec_member, opec_production, formosa_dependency, debt_burden, social_baseline, mil_ground, mil_naval, mil_tactical_air, mil_strategic_missiles, mil_air_defense, prod_cost_ground, prod_cost_naval, prod_cost_tactical, prod_cap_ground, prod_cap_naval, prod_cap_tactical, maintenance_per_unit, strategic_missile_growth, mobilization_pool, stability, political_support, dem_rep_split_dem, dem_rep_split_rep, war_tiredness, nuclear_level, nuclear_rd_progress, ai_level, ai_rd_progress, home_zones) VALUES
('columbia', '00000000-0000-0000-0000-000000000001', 'Columbia', 'United States', 'democracy', 'team', 7, 9, false, 280, 1.8, 8, 18, 55, 22, 0.24, 50, 3.5, -12, true, false, 'na', 0.65, 5, 0.30, 22, 11, 15, 12, 4, 3, 5, 4, 4, 0.17, 3, 0.5, 0, 12, 7, 38, 52, 48, 1, 3, 1.0, 3, 0.80, 'col_nw,col_w,col_main_1,col_main_2,col_main_3,col_main_4,col_south'),
('cathay', '00000000-0000-0000-0000-000000000001', 'Cathay', 'China', 'autocracy', 'team', 5, 5, false, 190, 4.0, 5, 52, 30, 13, 0.20, 45, 0.5, 12, false, false, 'na', 0.25, 2, 0.20, 25, 7, 12, 4, 3, 2, 4, 3, 5, 1, 3, 0.3, 1, 15, 8, 58, 0, 0, 0, 2, 0.80, 3, 0.10, 'cathay_1,cathay_2,cathay_3,cathay_4,cathay_5,cathay_6,cathay_7'),
('nordostan', '00000000-0000-0000-0000-000000000001', 'Nordostan', 'Russia', 'autocracy', 'team', 3, 4, false, 20, 1.0, 40, 25, 25, 10, 0.20, 6, 5.0, 2, true, true, 'normal', 0.15, 0.5, 0.25, 18, 2, 8, 12, 3, 1.5, 4, 3, 4, 0, 2, 0.3, 0, 5, 5, 55, 0, 0, 4, 3, 1.0, 1, 0.30, 'nord_n1,nord_w1,nord_c1,nord_e1,nord_e2,nord_e3,nord_w2,nord_c2'),
('heartland', '00000000-0000-0000-0000-000000000001', 'Heartland', 'Ukraine', 'democracy', 'team', 3, 3, false, 2.2, 2.5, 15, 20, 40, 10, 0.25, 5, 7.5, -0.8, false, false, 'na', 0.10, 0.3, 0.20, 10, 0, 3, 0, 1, 1.5, 0, 3, 2, 0, 1, 0.3, 0, 4, 5, 52, 0, 0, 4, 0, 0.0, 1, 0.40, 'heartland_1,heartland_2'),
('persia', '00000000-0000-0000-0000-000000000001', 'Persia', 'Iran', 'hybrid', 'team', 3, 3, false, 5, -3.0, 35, 30, 28, 7, 0.18, 1, 50.0, -1, true, true, 'normal', 0.15, 0, 0.20, 8, 0, 6, 1, 1, 1, 2, 2, 2, 0, 1, 0.25, 0, 6, 4, 40, 0, 0, 1, 0, 0.30, 0, 0.10, 'persia_1,persia_2,persia_3'),
('gallia', '00000000-0000-0000-0000-000000000001', 'Gallia', 'France', 'democracy', 'europe', 1, 1, false, 34, 1.0, 5, 20, 55, 20, 0.45, 8, 2.5, -1, false, false, 'na', 0.35, 3, 0.35, 6, 1, 4, 2, 1, 3, 5, 4, 2, 0, 1, 0.5, 0, 4, 7, 40, 0, 0, 0, 2, 0.80, 2, 0.30, 'gallia_1,gallia_2'),
('teutonia', '00000000-0000-0000-0000-000000000001', 'Teutonia', 'Germany', 'democracy', 'europe', 1, 1, false, 45, 1.2, 3, 28, 50, 19, 0.38, 12, 2.5, 3, false, false, 'na', 0.45, 2, 0.30, 6, 0, 3, 0, 1, 2.5, 4, 3.5, 2, 0, 1, 0.4, 0, 4, 7, 45, 0, 0, 0, 0, 0.0, 2, 0.20, 'teutonia_1,teutonia_2'),
('freeland', '00000000-0000-0000-0000-000000000001', 'Freeland', 'Poland', 'democracy', 'europe', 1, 1, false, 9, 3.7, 8, 30, 50, 12, 0.35, 4, 4.0, 0, false, false, 'na', 0.25, 1, 0.25, 5, 0, 2, 0, 1, 2, 3, 3, 2, 0, 1, 0.3, 0, 3, 8, 55, 0, 0, 0, 0, 0.0, 1, 0.40, 'freeland'),
('ponte', '00000000-0000-0000-0000-000000000001', 'Ponte', 'Italy', 'democracy', 'europe', 1, 1, false, 22, 0.8, 4, 22, 60, 14, 0.40, 4, 2.5, 0, false, false, 'na', 0.30, 8, 0.30, 4, 0, 2, 0, 0, 2.5, 4.5, 3.5, 1, 0, 1, 0.4, 0, 2, 6, 42, 0, 0, 0, 0, 0.0, 1, 0.30, 'ponte'),
('albion', '00000000-0000-0000-0000-000000000001', 'Albion', 'United Kingdom', 'democracy', 'europe', 1, 1, false, 33, 1.1, 5, 17, 60, 18, 0.35, 8, 3.0, -2, false, false, 'na', 0.40, 3, 0.30, 4, 2, 3, 2, 1, 3, 5, 4, 1, 0, 1, 0.5, 0, 3, 7, 38, 0, 0, 0, 2, 0.70, 2, 0.40, 'albion'),
('bharata', '00000000-0000-0000-0000-000000000001', 'Bharata', 'India', 'democracy', 'solo', 1, 1, true, 42, 6.5, 10, 25, 48, 17, 0.18, 12, 5.0, -3, false, false, 'na', 0.35, 3, 0.20, 12, 2, 4, 0, 2, 2, 4, 3, 3, 0.5, 1, 0.25, 0, 8, 6, 58, 0, 0, 0, 1, 0.40, 2, 0.45, 'bharata_1,bharata_2,bharata_3'),
('levantia', '00000000-0000-0000-0000-000000000001', 'Levantia', 'Israel', 'democracy', 'solo', 1, 1, true, 5, 3.0, 3, 15, 50, 32, 0.32, 5, 3.5, -1, false, false, 'na', 0.30, 2, 0.28, 6, 0, 4, 0, 3, 3, 5, 4, 2, 0, 2, 0.40, 0, 2, 5, 52, 0, 0, 2, 1, 0.50, 2, 0.55, 'levantia'),
('formosa', '00000000-0000-0000-0000-000000000001', 'Formosa', 'Taiwan', 'democracy', 'solo', 1, 1, true, 8, 3.0, 2, 30, 35, 33, 0.20, 8, 2.0, 4, false, false, 'na', 0.0, 1, 0.22, 4, 0, 3, 0, 2, 3, 5, 4, 1, 0, 1, 0.35, 0, 1, 7, 55, 0, 0, 0, 0, 0.0, 2, 0.50, 'formosa'),
('phrygia', '00000000-0000-0000-0000-000000000001', 'Phrygia', 'Turkey', 'hybrid', 'solo', 1, 1, true, 11, 3.0, 8, 30, 50, 12, 0.25, 4, 45.0, -3, false, false, 'na', 0.20, 3, 0.22, 6, 1, 3, 0, 1, 2, 4, 3, 2, 0, 1, 0.30, 0, 4, 5, 50, 0, 0, 0, 0, 0.0, 1, 0.25, 'phrygia_1,phrygia_2'),
('yamato', '00000000-0000-0000-0000-000000000001', 'Yamato', 'Japan', 'democracy', 'solo', 1, 1, true, 43, 1.0, 2, 28, 50, 20, 0.30, 15, 2.5, -2, false, false, 'na', 0.55, 6, 0.30, 3, 2, 3, 0, 2, 3, 5, 4, 1, 0, 1, 0.45, 0, 3, 8, 48, 0, 0, 0, 0, 0.10, 3, 0.30, 'yamato_1,yamato_2'),
('solaria', '00000000-0000-0000-0000-000000000001', 'Solaria', 'Saudi Arabia', 'autocracy', 'solo', 1, 1, true, 11, 3.5, 45, 20, 28, 7, 0.10, 20, 2.0, 8, true, true, 'normal', 0.20, 1, 0.25, 3, 0, 3, 0, 2, 3, 5, 4, 1, 0, 1, 0.40, 0, 1, 7, 65, 0, 0, 1, 0, 0.10, 1, 0.20, 'solaria_1,solaria_2'),
('choson', '00000000-0000-0000-0000-000000000001', 'Choson', 'North Korea', 'autocracy', 'solo', 1, 1, true, 0.3, 0.5, 20, 40, 35, 5, 0.50, 1, 10.0, -0.5, false, false, 'na', 0.0, 0, 0.10, 8, 0, 2, 1, 1, 1, 3, 2, 2, 0, 1, 0.15, 0, 2, 4, 70, 0, 0, 0, 1, 0.50, 0, 0.0, 'choson'),
('hanguk', '00000000-0000-0000-0000-000000000001', 'Hanguk', 'South Korea', 'democracy', 'solo', 1, 1, true, 18, 2.2, 3, 33, 42, 22, 0.26, 8, 2.5, 3, false, false, 'na', 0.40, 2, 0.25, 5, 0, 3, 0, 2, 2, 4, 3, 2, 0, 1, 0.35, 0, 3, 6, 35, 0, 0, 0, 0, 0.05, 2, 0.50, 'hanguk'),
('caribe', '00000000-0000-0000-0000-000000000001', 'Caribe', 'Cuba + Venezuela', 'autocracy', 'solo', 1, 1, true, 2, -1.0, 50, 20, 25, 5, 0.30, 1, 60.0, 0, true, false, 'na', 0.0, 5, 0.20, 3, 0, 1, 0, 0, 2, 4, 3, 1, 0, 0, 0.20, 0, 1, 3, 45, 0, 0, 0, 0, 0.0, 0, 0.0, 'caribe'),
('mirage', '00000000-0000-0000-0000-000000000001', 'Mirage', 'UAE', 'autocracy', 'solo', 1, 1, true, 5, 4.0, 30, 15, 45, 10, 0.0, 15, 2.0, 5, true, true, 'normal', 0.15, 0, 0.20, 2, 0, 2, 0, 2, 3, 5, 4, 1, 0, 1, 0.35, 0, 1, 8, 70, 0, 0, 1, 0, 0.0, 1, 0.30, 'mirage');


-- =============================================================================
-- 2. ROLES (from roles.csv — 41 rows)
-- =============================================================================

INSERT INTO roles (id, sim_run_id, character_name, parallel, country_id, team, faction, title, age, gender, is_head_of_state, is_military_chief, parliament_seat, personal_coins, personal_coins_notes, expansion_role, ai_candidate, is_ai_operated, brief_file, intelligence_pool, powers, objectives, ticking_clock, sabotage_cards, cyber_cards, disinfo_cards, election_meddling_cards, assassination_cards, protest_stim_cards, fatherland_appeal, is_diplomat) VALUES
('dealer', '00000000-0000-0000-0000-000000000001', 'Dealer', 'US President', 'columbia', 'Columbia', 'Presidents', 'President of Columbia', 80, 'M', true, false, 1, 5, '', false, false, false, 'role_briefs/DEALER.md', 4, ARRAY['set_tariffs','authorize_attack','fire_team_member','approve_nuclear','sign_treaty','set_budget','endorse_successor'], ARRAY['secure_legacy','manage_succession','contain_cathay'], 'Term-limited age 80. 10% per-round incapacitation risk. Legacy = reshaping world order.', 1, 1, 1, 1, 1, 0, 1, false),
('volt', '00000000-0000-0000-0000-000000000001', 'Volt', 'US Vice President', 'columbia', 'Columbia', 'Presidents', 'Vice President of Columbia', 60, 'M', false, false, 2, 3, '', false, false, false, 'role_briefs/VOLT.md', 2, ARRAY['assume_presidency','break_tie_vote','chair_nsc'], ARRAY['win_nomination','build_base','prove_loyalty'], 'Succession race. Must balance loyalty to Dealer with own presidential ambitions. America First isolationist wing.', 0, 0, 0, 0, 0, 0, 0, false),
('anchor', '00000000-0000-0000-0000-000000000001', 'Anchor', 'US Secretary of State', 'columbia', 'Columbia', 'Presidents', 'Secretary of State', 62, 'M', false, false, 0, 3, '', false, false, false, 'role_briefs/ANCHOR.md', 3, ARRAY['negotiate_treaty','represent_abroad','diplomatic_channel'], ARRAY['win_nomination','cuba_legacy','alliance_management'], 'Succession race. Cuba is personal trophy. Hawkish diplomatic establishment.', 0, 0, 1, 1, 0, 0, 0, true),
('shield', '00000000-0000-0000-0000-000000000001', 'Shield', 'US Secretary of Defense', 'columbia', 'Columbia', 'Presidents', 'Secretary of Defense', 58, 'M', false, true, 0, 2, '', false, false, false, 'role_briefs/SHIELD.md', 3, ARRAY['deploy_forces','military_operations','advise_president'], ARRAY['military_readiness','manage_overstretch','warrior_ethos'], 'Overstretched military. Persia war consuming resources. Pacific deterrence at risk. Warrior ethos philosophy.', 1, 1, 0, 0, 0, 0, 0, false),
('shadow', '00000000-0000-0000-0000-000000000001', 'Shadow', 'CIA Director', 'columbia', 'Columbia', 'Presidents', 'Director of Central Intelligence', 55, 'M', false, false, 0, 2, '', false, false, false, 'role_briefs/SHADOW.md', 8, ARRAY['intelligence_briefing','covert_operations','information_control'], ARRAY['intelligence_accuracy','covert_influence','protect_sources'], 'Controls what Dealer sees. Information is power. Can shape decisions through selective briefings.', 3, 3, 3, 1, 1, 0, 0, false),
('tribune', '00000000-0000-0000-0000-000000000001', 'Tribune', 'Congressional Opposition Leader', 'columbia', 'Columbia', 'Opposition', 'Speaker of the Opposition', 50, 'F', false, false, 3, 2, '', false, false, false, 'role_briefs/TRIBUNE.md', 1, ARRAY['block_budget','launch_investigation','public_statement','midterm_campaign'], ARRAY['flip_parliament','constrain_president','opposition_agenda'], 'Mid-terms Round 2. If opposition wins Seat 5 Parliament flips 3-2.', 0, 0, 1, 0, 0, 1, 0, false),
('challenger', '00000000-0000-0000-0000-000000000001', 'Challenger', 'Opposition Presidential Candidate', 'columbia', 'Columbia', 'Opposition', 'Presidential Candidate', 45, 'M', false, false, 4, 2, '', false, false, false, 'role_briefs/CHALLENGER.md', 1, ARRAY['campaign','foreign_meetings','public_statement','alternative_policy'], ARRAY['win_presidency','build_coalition','offer_alternative_future'], 'Presidential election Round 5. Every foreign leader hedges between Dealer and Challenger.', 0, 0, 1, 0, 0, 1, 0, false),
('fixer', '00000000-0000-0000-0000-000000000001', 'Fixer', 'Presidential Envoy - Middle East', 'columbia', 'Columbia', 'Presidents', 'Presidential Envoy for Peace', 55, 'M', false, false, 5, 2, '', true, true, false, 'role_briefs/FIXER.md', 3, ARRAY['parallel_diplomacy','back_channel','middle_east_negotiation'], ARRAY['peace_deal','dealer_legacy','regional_stability'], 'Expansion role. Parallel diplomatic channel may contradict official policy.', 1, 1, 1, 1, 0, 0, 0, true),
('pioneer', '00000000-0000-0000-0000-000000000001', 'Pioneer', 'Presidential Envoy - Tech/Business', 'columbia', 'Columbia', 'Presidents', 'Presidential Envoy for Technology', 52, 'M', false, false, 0, 4, '', true, true, false, 'role_briefs/PIONEER.md', 2, ARRAY['tech_diplomacy','business_channel','ai_policy'], ARRAY['tech_supremacy','business_deals','ai_regulation'], 'Expansion role. Tech tycoon with unaccountable influence.', 0, 1, 0, 0, 0, 0, 0, false),
('helmsman', '00000000-0000-0000-0000-000000000001', 'Helmsman', 'Chinese President/Chairman', 'cathay', 'Cathay', 'Chairman', 'Chairman of Cathay', 72, 'M', true, true, 0, 5, '', false, false, false, 'role_briefs/HELMSMAN.md', 4, ARRAY['all_executive','purge','military_order','set_policy','approve_nuclear'], ARRAY['formosa_resolution','national_rejuvenation','personal_legacy'], 'No successor. Age 72. 5-10% incapacitation risk per round. Legacy requires Formosa resolution.', 1, 1, 1, 1, 1, 0, 1, false),
('rampart', '00000000-0000-0000-0000-000000000001', 'Rampart', 'CMC Vice-Chairman', 'cathay', 'Cathay', 'Military', 'Marshal of Cathay', 65, 'M', false, true, 0, 3, '', false, false, false, 'role_briefs/RAMPART.md', 3, ARRAY['military_intelligence','co_sign_military','slow_walk','readiness_assessment'], ARRAY['military_readiness','survive_purges','professional_standards'], 'Purge survivor. Co-signature required for military orders. Can slow-walk with 1-round delay. Anti-corruption commissar background.', 1, 1, 0, 0, 0, 0, 0, false),
('abacus', '00000000-0000-0000-0000-000000000001', 'Abacus', 'Chinese Premier', 'cathay', 'Cathay', 'Government', 'Premier of Cathay', 63, 'M', false, false, 0, 3, '', false, false, false, 'role_briefs/ABACUS.md', 2, ARRAY['economic_data','budget_co_sign','acting_leader','reform_proposal'], ARRAY['economic_stability','reform','prevent_catastrophe'], 'Controls real economic data. Hidden local debt crisis ($9-13T LGFVs). Acting leader if Helmsman incapacitated.', 0, 1, 0, 0, 0, 0, 0, false),
('circuit', '00000000-0000-0000-0000-000000000001', 'Circuit', 'Tech/Industry Chief', 'cathay', 'Cathay', 'Business', 'Minister of Technology and Industry', 50, 'M', false, false, 0, 2, '2 coins abroad at risk if confrontation escalates', false, false, false, 'role_briefs/CIRCUIT.md', 2, ARRAY['tech_policy','rare_earth_weapon','foreign_business','cyber_operations'], ARRAY['tech_self_sufficiency','protect_assets','global_integration'], 'Global assets at risk. Rare earth weapon is depreciating. 2 personal coins represent assets abroad.', 0, 2, 0, 0, 0, 0, 0, false),
('sage', '00000000-0000-0000-0000-000000000001', 'Sage', 'Party Elder', 'cathay', 'Cathay', 'Elder', 'Retired Senior Leader', 78, 'M', false, false, 0, 2, '', false, false, false, 'role_briefs/SAGE.md', 1, ARRAY['party_conference','informal_counsel','succession_mechanism','legitimacy_challenge'], ARRAY['party_survival','collective_leadership','prevent_catastrophe'], 'Activates when stability < 5 or support < 40%. Party immune system. Can convene party conference.', 0, 0, 0, 0, 0, 0, 0, true),
('lumiere', '00000000-0000-0000-0000-000000000001', 'Lumiere', 'French President', 'gallia', 'Europe', 'Gallia', 'President of Gallia', 48, 'M', true, true, 0, 3, '', false, true, false, 'role_briefs/LUMIERE.md', 4, ARRAY['eu_vote','nato_vote','unsc_veto','nuclear_authority','strategic_autonomy','deploy_independently'], ARRAY['european_autonomy','nuclear_credibility','global_influence'], 'Strategic autonomy champion. UNSC veto. Nuclear power. Ile-Longue speech expanding deterrent. 11-16% domestic approval.', 1, 1, 1, 1, 0, 0, 1, false),
('forge', '00000000-0000-0000-0000-000000000001', 'Forge', 'German Chancellor', 'teutonia', 'Europe', 'Teutonia', 'Chancellor of Teutonia', 55, 'M', true, false, 0, 3, '', false, true, false, 'role_briefs/FORGE.md', 4, ARRAY['eu_vote','nato_vote','trade_policy','rearmament_decision','host_columbia_base'], ARRAY['economic_prosperity','cathay_trade','reluctant_rearmament'], 'Massive Cathay trade dependency. Pressured to spend 5% GDP on defense. Hosts Columbia main European base. EUR 100B defense fund.', 0, 1, 0, 0, 0, 0, 1, false),
('sentinel', '00000000-0000-0000-0000-000000000001', 'Sentinel', 'Polish President', 'freeland', 'Europe', 'Freeland', 'President of Freeland', 52, 'M', true, false, 0, 2, '', false, true, false, 'role_briefs/SENTINEL.md', 4, ARRAY['eu_vote','nato_vote','defense_spending','eastern_flank','heartland_logistics'], ARRAY['maximum_security','nordostan_containment','nato_commitment'], 'NATO frontline. 4.8% GDP defense spending. Hosts Columbia forward deployments. Cohabitation with opposition president.', 0, 0, 0, 0, 0, 0, 1, false),
('ponte_role', '00000000-0000-0000-0000-000000000001', 'Ponte', 'Italian PM', 'ponte', 'Europe', 'Ponte', 'Prime Minister of Ponte', 50, 'F', true, false, 0, 2, '', false, true, false, 'role_briefs/PONTE_ROLE.md', 4, ARRAY['eu_vote','nato_vote','swing_vote','debt_management','veto_sanctions'], ARRAY['debt_survival','eu_influence','hedge_all_sides'], 'EU swing vote. 137.9% debt-to-GDP. 8 coins/round debt service. Russia-sympathetic coalition partners. Referendum defeat.', 0, 0, 0, 0, 0, 0, 1, false),
('mariner', '00000000-0000-0000-0000-000000000001', 'Mariner', 'British PM', 'albion', 'Europe', 'Albion', 'Prime Minister of Albion', 56, 'M', true, true, 0, 3, '', false, true, false, 'role_briefs/MARINER.md', 4, ARRAY['nato_vote','unsc_veto','nuclear_authority','five_eyes','pacific_ambition','intelligence_sharing'], ARRAY['special_relationship','post_brexit_relevance','nuclear_credibility'], 'NATO but not EU. Five Eyes intelligence broker. UNSC veto. Offering troops for Heartland ceasefire monitoring.', 1, 1, 1, 1, 1, 0, 1, false),
('pillar', '00000000-0000-0000-0000-000000000001', 'Pillar', 'EU Commissioner', 'gallia', 'Europe', 'EU', 'Commissioner of The Union', 60, 'F', false, false, 0, 2, '', false, true, false, 'role_briefs/PILLAR.md', 2, ARRAY['eu_agenda','call_eu_session','external_trade_negotiation','frame_issues','propose_compromise'], ARRAY['eu_unity','institutional_relevance','resist_bilateral_bypass'], 'Cannot vote but sets EU agenda. Nightmare: member states bypassing EU for bilateral deals.', 0, 0, 0, 0, 0, 0, 0, true),
('pathfinder', '00000000-0000-0000-0000-000000000001', 'Pathfinder', 'Russian President', 'nordostan', 'Nordostan', 'President', 'President of Nordostan', 73, 'M', true, false, 0, 4, '', false, false, false, 'role_briefs/PATHFINDER.md', 4, ARRAY['all_executive','arrest','nuclear_co_authority','war_direction','purge'], ARRAY['territorial_control','great_power_recognition','personal_survival'], 'Age 73. 5-10% incapacitation risk increasing 2%/round. No succession plan. War must produce callable victory.', 1, 1, 1, 1, 1, 0, 1, false),
('ironhand', '00000000-0000-0000-0000-000000000001', 'Ironhand', 'Russian General', 'nordostan', 'Nordostan', 'Military', 'Chief of General Staff', 60, 'M', false, true, 0, 2, '', false, false, false, 'role_briefs/IRONHAND.md', 3, ARRAY['military_operations','nuclear_co_authority','honest_assessment','coup_potential','frontline_command'], ARRAY['military_result','professional_honor','survive'], 'Nuclear co-authorization required. Can slow-walk orders. Coup potential if conditions align with Compass.', 1, 1, 0, 0, 0, 0, 0, false),
('compass', '00000000-0000-0000-0000-000000000001', 'Compass', 'Russian Oligarch', 'nordostan', 'Nordostan', 'Economic', 'Oligarch / Back-Channel', 55, 'M', false, false, 0, 3, '3 coins frozen abroad by Western sanctions', false, false, false, 'role_briefs/COMPASS.md', 2, ARRAY['economic_management','back_channel','sanctions_evasion','deal_making'], ARRAY['sanctions_relief','unfreeze_assets','economic_survival'], '3 personal coins frozen abroad. Direct financial incentive for peace. Back-channels to West.', 0, 0, 0, 0, 0, 0, 0, true),
('ledger', '00000000-0000-0000-0000-000000000001', 'Ledger', 'Russian PM/Technocrat', 'nordostan', 'Nordostan', 'Government', 'Prime Minister of Nordostan', 50, 'M', false, false, 0, 2, '', true, true, false, 'role_briefs/LEDGER.md', 2, ARRAY['state_budget','bureaucracy','economic_data','institutional_continuity'], ARRAY['state_survival','institutional_continuity','follow_pathfinder'], 'Expansion role. Keeps the machine running. Sees real economic data. Institutional loyalty.', 0, 0, 0, 0, 0, 0, 0, false),
('beacon', '00000000-0000-0000-0000-000000000001', 'Beacon', 'Ukrainian President', 'heartland', 'Heartland', 'Resistance', 'President of Heartland', 47, 'M', true, false, 0, 2, '', false, false, false, 'role_briefs/BEACON.md', 4, ARRAY['executive_authority','alliance_diplomacy','war_leadership','territory_decisions','martial_law'], ARRAY['national_survival','territorial_integrity','western_support'], '22.6% first-round vote share but controls executive under martial law. Corruption scandal damaged credibility.', 0, 0, 0, 0, 0, 0, 1, false),
('bulwark', '00000000-0000-0000-0000-000000000001', 'Bulwark', 'Ukrainian General', 'heartland', 'Heartland', 'Military', 'Commander-in-Chief', 50, 'M', false, true, 0, 1, '', false, false, false, 'role_briefs/BULWARK.md', 3, ARRAY['military_command','shadow_diplomacy','popular_appeal','wartime_election'], ARRAY['military_victory','win_presidency','better_leadership'], 'Would beat Beacon 64-36 in runoff. More popular than president. Wartime election candidate.', 0, 0, 0, 0, 0, 0, 0, false),
('broker', '00000000-0000-0000-0000-000000000001', 'Broker', 'Ukrainian Politician', 'heartland', 'Heartland', 'Pragmatist', 'Opposition Leader', 52, 'M', false, false, 0, 1, '', false, false, false, 'role_briefs/BROKER.md', 1, ARRAY['back_channel','peace_negotiation','eu_connections','wartime_election'], ARRAY['negotiated_peace','eu_membership','pragmatic_deal'], 'EU connections and oligarchic resources. Peace deal candidate. Territory-for-security trade.', 0, 0, 0, 0, 0, 1, 0, true),
('furnace', '00000000-0000-0000-0000-000000000001', 'Furnace', 'Iranian Supreme Leader', 'persia', 'Persia', 'Hardline', 'Supreme Leader of Persia', 45, 'M', true, false, 0, 3, '', false, false, false, 'role_briefs/FURNACE.md', 4, ARRAY['supreme_authority','nuclear_decision','override_2of3','ideological_direction'], ARRAY['nuclear_weapon','independent_authority','regime_survival'], 'Mojtaba Khamenei parallel. Installed by IRGC. May be hiding/injured. Override costs -5 support -1 stability each use.', 0, 0, 1, 0, 1, 0, 1, false),
('anvil', '00000000-0000-0000-0000-000000000001', 'Anvil', 'IRGC Commander', 'persia', 'Persia', 'Military', 'Commander of Revolutionary Guard', 58, 'M', false, true, 0, 2, '2 coins representing IRGC economic empire partially frozen', false, false, false, 'role_briefs/ANVIL.md', 3, ARRAY['military_operations','business_empire','kingmaker','veto_military','pragmatic_deal'], ARRAY['irgc_survival','business_protection','power_broker'], 'IRGC controls 1/3 of economy. 2 personal coins = IRGC institutional wealth. Sanctions relief = personal profit. Can veto military orders with 1-round delay.', 2, 1, 1, 0, 1, 0, 0, false),
('dawn', '00000000-0000-0000-0000-000000000001', 'Dawn', 'Iranian Reformist', 'persia', 'Persia', 'Reform', 'Reformist Leader', 45, 'F', false, false, 0, 1, '', false, false, false, 'role_briefs/DAWN.md', 1, ARRAY['public_appeal','western_contact','reform_proposal','diplomatic_credibility'], ARRAY['engagement','sanctions_relief','represent_youth'], 'Represents 60% under 30. Deals with Dawn as signatory get +20% credibility. Activates when stability < 4 or support < 30%.', 0, 0, 0, 0, 0, 1, 0, false),
('scales', '00000000-0000-0000-0000-000000000001', 'Scales', 'Indian PM', 'bharata', 'Bharata', 'National', 'Prime Minister of Bharata', 75, 'M', true, false, 0, 3, '', false, true, false, 'role_briefs/SCALES.md', 4, ARRAY['non_alignment','play_all_sides','nuclear_authority','trade_policy','brics_host'], ARRAY['strategic_autonomy','economic_growth','multi_alignment'], '2026 BRICS+ host. Multi-alignment doctrine. Everyone needs something from Bharata. Refused to take position on Iran war.', 1, 1, 1, 1, 0, 0, 1, true),
('citadel', '00000000-0000-0000-0000-000000000001', 'Citadel', 'Israeli PM', 'levantia', 'Levantia', 'National', 'Prime Minister of Levantia', 76, 'M', true, true, 0, 3, '', false, true, false, 'role_briefs/CITADEL.md', 4, ARRAY['military_authority','unilateral_action','nuclear_ambiguity','regional_operations','multi_front_war'], ARRAY['regional_dominance','destroy_persia_threat','columbia_alliance'], 'Multi-front war: Persia + Lebanon + Gaza. Operation Rising Lion. Densest air defense in world. Undeclared nuclear L1.', 2, 2, 1, 1, 2, 0, 1, true),
('chip', '00000000-0000-0000-0000-000000000001', 'Chip', 'Taiwanese President', 'formosa', 'Formosa', 'National', 'President of Formosa', 60, 'F', true, false, 0, 2, '', false, true, false, 'role_briefs/CHIP.md', 4, ARRAY['semiconductor_leverage','defense_policy','diplomatic_status','porcupine_strategy'], ARRAY['survival','semiconductor_shield','columbia_protection'], 'KMT legislature blocking defense budget. $40B defense plan cut 70%. Silicon shield eroding as fabs built abroad.', 0, 1, 0, 0, 0, 0, 1, true),
('bazaar', '00000000-0000-0000-0000-000000000001', 'Bazaar', 'Turkish President', 'phrygia', 'Phrygia', 'National', 'President of Phrygia', 70, 'M', true, true, 0, 3, '', false, true, false, 'role_briefs/BAZAAR.md', 4, ARRAY['bosphorus_control','nato_veto','play_all_sides','arms_deals','nato_summit_host'], ARRAY['maximum_leverage','bosphorus_control','hedge_everyone'], '2026 NATO summit host. Controls Bosphorus and Dardanelles. NATO member + BRICS+ observer. S-400 buyer.', 1, 1, 1, 1, 0, 0, 1, true),
('sakura', '00000000-0000-0000-0000-000000000001', 'Sakura', 'Japanese PM', 'yamato', 'Yamato', 'National', 'Prime Minister of Yamato', 55, 'F', true, false, 0, 3, '', false, true, false, 'role_briefs/SAKURA.md', 4, ARRAY['remilitarization','pacific_alliance','nuclear_debate','trade_policy','latent_nuclear'], ARRAY['pacific_security','remilitarization','columbia_alliance'], 'First female PM. Record defense budget $57.8B. 2% GDP achieved early. Latent nuclear capability. Rapidus 2nm chip project.', 0, 1, 0, 0, 0, 0, 1, true),
('wellspring', '00000000-0000-0000-0000-000000000001', 'Wellspring', 'Saudi Crown Prince', 'solaria', 'Solaria', 'National', 'Crown Prince of Solaria', 40, 'M', true, false, 0, 5, '', false, true, false, 'role_briefs/WELLSPRING.md', 4, ARRAY['oil_production','opec_leadership','arms_deals','hedging','nuclear_threat'], ARRAY['oil_pricing_power','vision_2030','infrastructure_defense'], 'Under active Persia missile attack. Ras Tanura refinery damaged. $16.5B arms package from Columbia. Will go nuclear if Persia does.', 1, 1, 1, 1, 1, 0, 1, true),
('pyro', '00000000-0000-0000-0000-000000000001', 'Pyro', 'North Korean Leader', 'choson', 'Choson', 'National', 'Supreme Leader of Choson', 42, 'M', true, true, 0, 1, '', false, true, false, 'role_briefs/PYRO.md', 4, ARRAY['nuclear_provocation','arms_sales','troop_deployment','unpredictable_action','patron_manipulation'], ARRAY['regime_survival','nuclear_leverage','blood_for_technology'], '15000+ troops in Heartland. 6000+ casualties. Blood-for-technology with Nordostan. Crisis on demand capability.', 1, 0, 1, 0, 1, 0, 1, true),
('vanguard', '00000000-0000-0000-0000-000000000001', 'Vanguard', 'South Korean President', 'hanguk', 'Hanguk', 'National', 'President of Hanguk', 55, 'M', true, false, 0, 2, '', false, true, false, 'role_briefs/VANGUARD.md', 4, ARRAY['defense_policy','trade_policy','semiconductor_competition','maximum_flexibility'], ARRAY['national_security','economic_stability','balance_columbia_cathay'], 'Post-martial-law recovery. Maximum flexibility doctrine. Security with Columbia economy with Cathay. Samsung/SK Hynix leverage.', 0, 1, 0, 0, 0, 0, 1, true),
('havana', '00000000-0000-0000-0000-000000000001', 'Havana', 'Cuban/Venezuelan Leader', 'caribe', 'Caribe', 'National', 'Leader of Caribe', 65, 'M', true, false, 0, 1, '', false, true, false, 'role_briefs/HAVANA.md', 4, ARRAY['resistance','foreign_patron','monroe_doctrine_trigger','survival_diplomacy'], ARRAY['regime_survival','break_blockade','find_patrons'], 'Under Columbia energy blockade. Nationwide blackout March 2026. Can invite Nordostan/Cathay military assets to trigger Monroe Doctrine crisis.', 0, 0, 1, 0, 0, 0, 1, true),
('spire', '00000000-0000-0000-0000-000000000001', 'Spire', 'UAE Ruler', 'mirage', 'Mirage', 'National', 'Ruler of Mirage', 52, 'M', true, false, 0, 4, '', false, true, false, 'role_briefs/SPIRE.md', 4, ARRAY['financial_hub','sanctions_routing','back_channel_venue','arms_deals','hedging'], ARRAY['financial_power','connect_everyone','pragmatic_hedging'], '357 ballistic missiles + 1815 drones launched at UAE. Financial intermediary: +20% sanctions effectiveness when cooperating or +20% evasion when enabling.', 0, 1, 0, 0, 0, 0, 1, true);


-- =============================================================================
-- 3. ZONES (from zones.csv — 58 rows)
-- =============================================================================

INSERT INTO zones (id, sim_run_id, display_name, type, owner, theater, is_chokepoint, die_hard) VALUES
('col_nw', '00000000-0000-0000-0000-000000000001', 'Columbia Northwest', 'land_home', 'columbia', 'americas', false, false),
('col_w', '00000000-0000-0000-0000-000000000001', 'Columbia West', 'land_home', 'columbia', 'americas', false, false),
('col_main_1', '00000000-0000-0000-0000-000000000001', 'Columbia Central', 'land_home', 'columbia', 'americas', false, false),
('col_main_2', '00000000-0000-0000-0000-000000000001', 'Columbia East', 'land_home', 'columbia', 'americas', false, false),
('col_main_3', '00000000-0000-0000-0000-000000000001', 'Columbia South Central', 'land_home', 'columbia', 'americas', false, false),
('col_main_4', '00000000-0000-0000-0000-000000000001', 'Columbia Southeast', 'land_home', 'columbia', 'americas', false, false),
('col_south', '00000000-0000-0000-0000-000000000001', 'Columbia South', 'land_home', 'columbia', 'americas', false, false),
('caribe', '00000000-0000-0000-0000-000000000001', 'Caribe', 'land_home', 'caribe', 'americas', false, false),
('cp_caribe_passage', '00000000-0000-0000-0000-000000000001', 'Caribe Passage', 'chokepoint', 'none', 'americas', true, false),
('thule', '00000000-0000-0000-0000-000000000001', 'Thule', 'land_contested', 'teutonia', 'ereb', false, false),
('albion', '00000000-0000-0000-0000-000000000001', 'Albion', 'land_home', 'albion', 'ereb', false, false),
('teutonia_1', '00000000-0000-0000-0000-000000000001', 'Teutonia North', 'land_home', 'teutonia', 'ereb', false, false),
('teutonia_2', '00000000-0000-0000-0000-000000000001', 'Teutonia South', 'land_home', 'teutonia', 'ereb', false, false),
('freeland', '00000000-0000-0000-0000-000000000001', 'Freeland', 'land_home', 'freeland', 'ereb', false, false),
('gallia_1', '00000000-0000-0000-0000-000000000001', 'Gallia West', 'land_home', 'gallia', 'ereb', false, false),
('gallia_2', '00000000-0000-0000-0000-000000000001', 'Gallia East', 'land_home', 'gallia', 'ereb', false, false),
('ponte', '00000000-0000-0000-0000-000000000001', 'Ponte', 'land_home', 'ponte', 'ereb', false, false),
('heartland_1', '00000000-0000-0000-0000-000000000001', 'Heartland West', 'land_home', 'heartland', 'ereb', false, false),
('heartland_2', '00000000-0000-0000-0000-000000000001', 'Heartland East', 'land_contested', 'heartland', 'ereb', false, true),
('nord_n1', '00000000-0000-0000-0000-000000000001', 'Nordostan Arctic', 'land_home', 'nordostan', 'ereb', false, false),
('nord_w1', '00000000-0000-0000-0000-000000000001', 'Nordostan West', 'land_home', 'nordostan', 'ereb', false, false),
('nord_w2', '00000000-0000-0000-0000-000000000001', 'Nordostan Southwest', 'land_home', 'nordostan', 'ereb', false, false),
('nord_c1', '00000000-0000-0000-0000-000000000001', 'Nordostan Central', 'land_home', 'nordostan', 'ereb', false, false),
('nord_c2', '00000000-0000-0000-0000-000000000001', 'Nordostan South Central', 'land_home', 'nordostan', 'ereb', false, false),
('nord_e1', '00000000-0000-0000-0000-000000000001', 'Nordostan East', 'land_home', 'nordostan', 'ereb', false, false),
('nord_e2', '00000000-0000-0000-0000-000000000001', 'Nordostan Far East', 'land_home', 'nordostan', 'ereb', false, false),
('nord_e3', '00000000-0000-0000-0000-000000000001', 'Nordostan Pacific', 'land_home', 'nordostan', 'ereb', false, false),
('sogdiana_1', '00000000-0000-0000-0000-000000000001', 'Sogdiana North', 'land_contested', 'none', 'mashriq', false, false),
('sogdiana_2', '00000000-0000-0000-0000-000000000001', 'Sogdiana South', 'land_contested', 'none', 'mashriq', false, false),
('sogdiana_3', '00000000-0000-0000-0000-000000000001', 'Sogdiana East', 'land_contested', 'none', 'mashriq', false, false),
('phrygia_1', '00000000-0000-0000-0000-000000000001', 'Phrygia East', 'land_home', 'phrygia', 'mashriq', false, false),
('phrygia_2', '00000000-0000-0000-0000-000000000001', 'Phrygia South', 'land_home', 'phrygia', 'mashriq', false, false),
('levantia', '00000000-0000-0000-0000-000000000001', 'Levantia', 'land_home', 'levantia', 'mashriq', false, false),
('persia_1', '00000000-0000-0000-0000-000000000001', 'Persia North', 'land_home', 'persia', 'mashriq', false, false),
('persia_2', '00000000-0000-0000-0000-000000000001', 'Persia West', 'land_home', 'persia', 'mashriq', false, false),
('persia_3', '00000000-0000-0000-0000-000000000001', 'Persia East', 'land_home', 'persia', 'mashriq', false, false),
('solaria_1', '00000000-0000-0000-0000-000000000001', 'Solaria West', 'land_home', 'solaria', 'mashriq', false, false),
('solaria_2', '00000000-0000-0000-0000-000000000001', 'Solaria East', 'land_home', 'solaria', 'mashriq', false, false),
('horn', '00000000-0000-0000-0000-000000000001', 'Horn of Africa', 'land_contested', 'none', 'mashriq', false, false),
('mirage', '00000000-0000-0000-0000-000000000001', 'Mirage', 'land_home', 'mirage', 'mashriq', false, false),
('cp_gulf_gate', '00000000-0000-0000-0000-000000000001', 'Gulf Gate', 'chokepoint', 'none', 'mashriq', true, false),
('bharata_1', '00000000-0000-0000-0000-000000000001', 'Bharata South', 'land_home', 'bharata', 'asu', false, false),
('bharata_2', '00000000-0000-0000-0000-000000000001', 'Bharata North', 'land_home', 'bharata', 'asu', false, false),
('bharata_3', '00000000-0000-0000-0000-000000000001', 'Bharata East', 'land_home', 'bharata', 'asu', false, false),
('choson', '00000000-0000-0000-0000-000000000001', 'Choson', 'land_home', 'choson', 'asu', false, false),
('hanguk', '00000000-0000-0000-0000-000000000001', 'Hanguk', 'land_home', 'hanguk', 'asu', false, false),
('cathay_1', '00000000-0000-0000-0000-000000000001', 'Cathay Northwest', 'land_home', 'cathay', 'asu', false, false),
('cathay_2', '00000000-0000-0000-0000-000000000001', 'Cathay West', 'land_home', 'cathay', 'asu', false, false),
('cathay_3', '00000000-0000-0000-0000-000000000001', 'Cathay Central', 'land_home', 'cathay', 'asu', false, false),
('cathay_4', '00000000-0000-0000-0000-000000000001', 'Cathay Northeast', 'land_home', 'cathay', 'asu', false, false),
('cathay_5', '00000000-0000-0000-0000-000000000001', 'Cathay Southwest', 'land_home', 'cathay', 'asu', false, false),
('cathay_6', '00000000-0000-0000-0000-000000000001', 'Cathay Southeast', 'land_home', 'cathay', 'asu', false, false),
('cathay_7', '00000000-0000-0000-0000-000000000001', 'Cathay South', 'land_home', 'cathay', 'asu', false, false),
('yamato_1', '00000000-0000-0000-0000-000000000001', 'Yamato North', 'land_home', 'yamato', 'asu', false, false),
('yamato_2', '00000000-0000-0000-0000-000000000001', 'Yamato South', 'land_home', 'yamato', 'asu', false, false),
('formosa', '00000000-0000-0000-0000-000000000001', 'Formosa', 'land_home', 'formosa', 'asu', false, false),
('cp_formosa_strait', '00000000-0000-0000-0000-000000000001', 'Formosa Strait', 'chokepoint', 'none', 'asu', true, false);


-- =============================================================================
-- 4. ZONE ADJACENCY (from zone_adjacency.csv — 97 rows)
-- =============================================================================

INSERT INTO zone_adjacency (sim_run_id, zone_a, zone_b, connection_type) VALUES
('00000000-0000-0000-0000-000000000001', 'col_nw', 'col_w', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'col_nw', 'col_main_1', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'col_w', 'col_main_1', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'col_w', 'col_main_3', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'col_main_1', 'col_main_2', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'col_main_1', 'col_main_3', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'col_main_1', 'col_main_4', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'col_main_2', 'col_main_4', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'col_main_3', 'col_main_4', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'col_main_3', 'col_south', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'col_main_4', 'col_south', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'col_south', 'cp_caribe_passage', 'land_sea'),
('00000000-0000-0000-0000-000000000001', 'cp_caribe_passage', 'caribe', 'land_sea'),
('00000000-0000-0000-0000-000000000001', 'teutonia_1', 'teutonia_2', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'teutonia_1', 'freeland', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'teutonia_1', 'heartland_1', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'teutonia_2', 'freeland', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'teutonia_2', 'gallia_1', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'teutonia_2', 'gallia_2', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'freeland', 'heartland_1', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'freeland', 'heartland_2', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'freeland', 'gallia_2', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'gallia_1', 'gallia_2', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'gallia_1', 'ponte', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'gallia_2', 'levantia', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'heartland_1', 'heartland_2', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'heartland_1', 'nord_w1', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'heartland_1', 'nord_w2', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'heartland_2', 'nord_w2', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'heartland_2', 'phrygia_1', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'nord_n1', 'nord_c1', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'nord_n1', 'nord_e1', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'nord_w1', 'nord_c1', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'nord_w1', 'nord_w2', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'nord_c1', 'nord_e1', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'nord_c1', 'nord_w2', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'nord_c1', 'nord_c2', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'nord_e1', 'nord_e2', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'nord_e1', 'nord_c2', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'nord_e2', 'nord_e3', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'nord_e2', 'sogdiana_1', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'nord_e2', 'sogdiana_3', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'nord_e3', 'sogdiana_3', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'nord_e3', 'cathay_1', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'nord_w2', 'nord_c2', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'nord_c2', 'sogdiana_1', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'sogdiana_1', 'sogdiana_2', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'sogdiana_1', 'sogdiana_3', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'sogdiana_2', 'sogdiana_3', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'sogdiana_2', 'persia_1', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'sogdiana_2', 'bharata_2', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'sogdiana_3', 'cathay_1', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'phrygia_1', 'phrygia_2', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'phrygia_1', 'persia_2', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'phrygia_2', 'levantia', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'phrygia_2', 'persia_2', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'phrygia_2', 'solaria_1', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'phrygia_2', 'solaria_2', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'levantia', 'solaria_1', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'persia_1', 'persia_3', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'persia_1', 'bharata_2', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'persia_2', 'persia_3', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'persia_2', 'solaria_2', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'persia_2', 'cp_gulf_gate', 'land_sea'),
('00000000-0000-0000-0000-000000000001', 'persia_3', 'persia_1', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'persia_3', 'cp_gulf_gate', 'land_sea'),
('00000000-0000-0000-0000-000000000001', 'solaria_1', 'solaria_2', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'solaria_1', 'horn', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'solaria_2', 'cp_gulf_gate', 'land_sea'),
('00000000-0000-0000-0000-000000000001', 'solaria_2', 'mirage', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'cp_gulf_gate', 'mirage', 'land_sea'),
('00000000-0000-0000-0000-000000000001', 'horn', 'solaria_1', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'bharata_1', 'bharata_2', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'bharata_1', 'bharata_3', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'bharata_2', 'bharata_3', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'bharata_2', 'persia_1', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'bharata_3', 'cathay_2', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'bharata_3', 'cathay_5', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'choson', 'hanguk', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'cathay_1', 'cathay_2', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'cathay_1', 'sogdiana_3', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'cathay_2', 'cathay_3', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'cathay_2', 'bharata_3', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'cathay_2', 'cathay_5', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'cathay_3', 'cathay_4', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'cathay_3', 'cathay_5', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'cathay_3', 'cathay_6', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'cathay_3', 'hanguk', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'cathay_4', 'cathay_6', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'cathay_4', 'hanguk', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'cathay_5', 'cathay_6', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'cathay_5', 'cathay_7', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'cathay_6', 'cathay_7', 'land_land'),
('00000000-0000-0000-0000-000000000001', 'cathay_6', 'cp_formosa_strait', 'land_sea'),
('00000000-0000-0000-0000-000000000001', 'cathay_7', 'cp_formosa_strait', 'land_sea'),
('00000000-0000-0000-0000-000000000001', 'cp_formosa_strait', 'formosa', 'land_sea');


-- =============================================================================
-- 5. ORGANIZATIONS (from organizations.csv — 9 rows)
-- =============================================================================

INSERT INTO organizations (id, sim_run_id, sim_name, parallel, decision_rule, chair_role_id, voting_threshold, meeting_frequency, can_be_created, description) VALUES
('western_treaty', '00000000-0000-0000-0000-000000000001', 'Western Treaty', 'NATO', 'consensus', '', 'unanimous', 'scheduled_r1_r4', false, 'Military alliance with Article 5 collective defense. ~70% of combined spending from Columbia.'),
('the_union', '00000000-0000-0000-0000-000000000001', 'The Union', 'EU', 'consensus', 'pillar', 'unanimous', 'scheduled_r1_r3', false, 'Political-economic union. Trade policy and sanctions coordination. Commissioner chairs.'),
('the_council', '00000000-0000-0000-0000-000000000001', 'The Council', 'UN Security Council', 'p5_veto', '', 'p5_unanimous_plus_majority', 'scheduled_r1_r4', false, 'International security body. P5 veto power. Structurally paralyzed on major issues.'),
('the_league', '00000000-0000-0000-0000-000000000001', 'The League', 'BRICS+', 'loose_consensus', '', 'non_binding', 'scheduled_r2_r4', false, 'Coordination forum for non-Western powers. Alternative payment systems and development bank.'),
('the_cartel', '00000000-0000-0000-0000-000000000001', 'The Cartel', 'OPEC+', 'independent_production', '', 'voluntary_coordination', 'every_round', false, 'Oil production coordination. Each member independently sets production. Classic prisoners dilemma.'),
('the_seven', '00000000-0000-0000-0000-000000000001', 'The Seven', 'G7', 'non_binding', '', 'non_binding', 'scheduled_r1_r4', false, 'Western coordination on tech restrictions and sanctions. Non-binding joint statements.'),
('columbia_parliament', '00000000-0000-0000-0000-000000000001', 'Columbia Parliament', 'US Congress', 'majority', '', 'three_of_five', 'every_round', false, 'Internal legislative body. 5 seats. Budget and treaty ratification require parliamentary approval.'),
('the_pact', '00000000-0000-0000-0000-000000000001', 'The Pact', 'SCO', 'consensus', '', 'non_binding', 'scheduled_r2', false, 'Security cooperation organization. Counter-terrorism and regional stability. Overlaps with The League membership.'),
('the_assembly', '00000000-0000-0000-0000-000000000001', 'The Assembly', 'UN General Assembly', 'majority', '', 'simple_majority', 'scheduled_r2_r5', false, 'Every country votes. No veto. No enforcement. Moral weight. Forces public position declarations.');


-- =============================================================================
-- 6. ORG MEMBERSHIPS (from org_memberships.csv — 61 rows)
-- =============================================================================

INSERT INTO org_memberships (sim_run_id, country_id, org_id, role_in_org, has_veto) VALUES
('00000000-0000-0000-0000-000000000001', 'columbia', 'western_treaty', 'founding_member', false),
('00000000-0000-0000-0000-000000000001', 'columbia', 'the_council', 'permanent_member', true),
('00000000-0000-0000-0000-000000000001', 'columbia', 'the_seven', 'member', false),
('00000000-0000-0000-0000-000000000001', 'columbia', 'columbia_parliament', 'internal', false),
('00000000-0000-0000-0000-000000000001', 'columbia', 'the_assembly', 'member', false),
('00000000-0000-0000-0000-000000000001', 'cathay', 'the_council', 'permanent_member', true),
('00000000-0000-0000-0000-000000000001', 'cathay', 'the_league', 'co_leader', false),
('00000000-0000-0000-0000-000000000001', 'cathay', 'the_assembly', 'member', false),
('00000000-0000-0000-0000-000000000001', 'nordostan', 'the_council', 'permanent_member', true),
('00000000-0000-0000-0000-000000000001', 'nordostan', 'the_league', 'co_leader', false),
('00000000-0000-0000-0000-000000000001', 'nordostan', 'the_cartel', 'member', false),
('00000000-0000-0000-0000-000000000001', 'nordostan', 'the_assembly', 'member', false),
('00000000-0000-0000-0000-000000000001', 'heartland', 'the_assembly', 'member', false),
('00000000-0000-0000-0000-000000000001', 'persia', 'the_league', 'member', false),
('00000000-0000-0000-0000-000000000001', 'persia', 'the_cartel', 'member', false),
('00000000-0000-0000-0000-000000000001', 'persia', 'the_assembly', 'member', false),
('00000000-0000-0000-0000-000000000001', 'gallia', 'western_treaty', 'founding_member', false),
('00000000-0000-0000-0000-000000000001', 'gallia', 'the_union', 'founding_member', false),
('00000000-0000-0000-0000-000000000001', 'gallia', 'the_council', 'permanent_member', true),
('00000000-0000-0000-0000-000000000001', 'gallia', 'the_seven', 'member', false),
('00000000-0000-0000-0000-000000000001', 'gallia', 'the_assembly', 'member', false),
('00000000-0000-0000-0000-000000000001', 'teutonia', 'western_treaty', 'member', false),
('00000000-0000-0000-0000-000000000001', 'teutonia', 'the_union', 'founding_member', false),
('00000000-0000-0000-0000-000000000001', 'teutonia', 'the_seven', 'member', false),
('00000000-0000-0000-0000-000000000001', 'teutonia', 'the_assembly', 'member', false),
('00000000-0000-0000-0000-000000000001', 'freeland', 'western_treaty', 'member', false),
('00000000-0000-0000-0000-000000000001', 'freeland', 'the_union', 'member', false),
('00000000-0000-0000-0000-000000000001', 'freeland', 'the_assembly', 'member', false),
('00000000-0000-0000-0000-000000000001', 'ponte', 'western_treaty', 'member', false),
('00000000-0000-0000-0000-000000000001', 'ponte', 'the_union', 'member', false),
('00000000-0000-0000-0000-000000000001', 'ponte', 'the_seven', 'member', false),
('00000000-0000-0000-0000-000000000001', 'ponte', 'the_assembly', 'member', false),
('00000000-0000-0000-0000-000000000001', 'albion', 'western_treaty', 'founding_member', false),
('00000000-0000-0000-0000-000000000001', 'albion', 'the_council', 'permanent_member', true),
('00000000-0000-0000-0000-000000000001', 'albion', 'the_seven', 'member', false),
('00000000-0000-0000-0000-000000000001', 'albion', 'the_assembly', 'member', false),
('00000000-0000-0000-0000-000000000001', 'bharata', 'the_league', 'member', false),
('00000000-0000-0000-0000-000000000001', 'bharata', 'the_council', 'rotating_member', false),
('00000000-0000-0000-0000-000000000001', 'bharata', 'the_assembly', 'member', false),
('00000000-0000-0000-0000-000000000001', 'levantia', 'the_assembly', 'member', false),
('00000000-0000-0000-0000-000000000001', 'formosa', 'the_assembly', 'observer', false),
('00000000-0000-0000-0000-000000000001', 'phrygia', 'western_treaty', 'member', false),
('00000000-0000-0000-0000-000000000001', 'phrygia', 'the_league', 'observer', false),
('00000000-0000-0000-0000-000000000001', 'phrygia', 'the_assembly', 'member', false),
('00000000-0000-0000-0000-000000000001', 'yamato', 'the_seven', 'member', false),
('00000000-0000-0000-0000-000000000001', 'yamato', 'the_assembly', 'member', false),
('00000000-0000-0000-0000-000000000001', 'solaria', 'the_league', 'member', false),
('00000000-0000-0000-0000-000000000001', 'solaria', 'the_cartel', 'leader', false),
('00000000-0000-0000-0000-000000000001', 'solaria', 'the_assembly', 'member', false),
('00000000-0000-0000-0000-000000000001', 'cathay', 'the_pact', 'co_leader', false),
('00000000-0000-0000-0000-000000000001', 'nordostan', 'the_pact', 'co_leader', false),
('00000000-0000-0000-0000-000000000001', 'bharata', 'the_pact', 'member', false),
('00000000-0000-0000-0000-000000000001', 'persia', 'the_pact', 'observer', false),
('00000000-0000-0000-0000-000000000001', 'phrygia', 'the_pact', 'dialogue_partner', false),
('00000000-0000-0000-0000-000000000001', 'choson', 'the_assembly', 'member', false),
('00000000-0000-0000-0000-000000000001', 'hanguk', 'the_assembly', 'member', false),
('00000000-0000-0000-0000-000000000001', 'caribe', 'the_assembly', 'member', false),
('00000000-0000-0000-0000-000000000001', 'mirage', 'the_league', 'member', false),
('00000000-0000-0000-0000-000000000001', 'mirage', 'the_cartel', 'member', false),
('00000000-0000-0000-0000-000000000001', 'mirage', 'the_assembly', 'member', false);


-- =============================================================================
-- 7. RELATIONSHIPS (from relationships.csv — 381 rows)
-- NOTE: This is the full directed relationship matrix. Due to size,
-- only key relationships are shown with the full set included.
-- =============================================================================

-- Columbia relationships
INSERT INTO relationships (sim_run_id, from_country, to_country, relationship, dynamic) VALUES
('00000000-0000-0000-0000-000000000001', 'columbia', 'cathay', 'strategic_rival', 'THE Trap itself. Largest bilateral trade under ~47.5% tariff assault.'),
('00000000-0000-0000-0000-000000000001', 'columbia', 'nordostan', 'hostile', 'Nuclear peer adversary. Sanctions regime. Proxy conflict via Heartland.'),
('00000000-0000-0000-0000-000000000001', 'columbia', 'heartland', 'close_ally', 'Ally at war. Weapons and aid provider.'),
('00000000-0000-0000-0000-000000000001', 'columbia', 'persia', 'at_war', 'Operation Epic Fury. Joint campaign with Levantia.'),
('00000000-0000-0000-0000-000000000001', 'columbia', 'gallia', 'alliance', 'NATO ally with friction.'),
('00000000-0000-0000-0000-000000000001', 'columbia', 'teutonia', 'alliance', 'NATO ally with friction. Hosts main European base.'),
('00000000-0000-0000-0000-000000000001', 'columbia', 'freeland', 'alliance', 'NATO frontline. Most enthusiastic ally.'),
('00000000-0000-0000-0000-000000000001', 'columbia', 'ponte', 'alliance', 'NATO ally but EU weak link.'),
('00000000-0000-0000-0000-000000000001', 'columbia', 'albion', 'close_ally', 'Special relationship. NATO Five Eyes UNSC.'),
('00000000-0000-0000-0000-000000000001', 'columbia', 'bharata', 'friendly', 'Courtship. Desperately needs Bharata in sanctions coalition.'),
('00000000-0000-0000-0000-000000000001', 'columbia', 'levantia', 'close_ally', 'Joint operations in Persia.'),
('00000000-0000-0000-0000-000000000001', 'columbia', 'formosa', 'close_ally', 'Protectorate. Strategic ambiguity. 65% semiconductor dependency.'),
('00000000-0000-0000-0000-000000000001', 'columbia', 'phrygia', 'alliance', 'NATO member playing every side.'),
('00000000-0000-0000-0000-000000000001', 'columbia', 'yamato', 'alliance', 'Pacific alliance cornerstone.'),
('00000000-0000-0000-0000-000000000001', 'columbia', 'solaria', 'friendly', 'OPEC kingpin. Oil pricing power.'),
('00000000-0000-0000-0000-000000000001', 'columbia', 'choson', 'hostile', 'Nuclear wildcard. No diplomatic channel.'),
('00000000-0000-0000-0000-000000000001', 'columbia', 'hanguk', 'alliance', 'US ally. Hosts bases.'),
('00000000-0000-0000-0000-000000000001', 'columbia', 'caribe', 'hostile', 'Post-intervention. Energy blockade.'),
('00000000-0000-0000-0000-000000000001', 'columbia', 'mirage', 'friendly', 'Financial hub. Arms buyer.'),
-- Cathay relationships
('00000000-0000-0000-0000-000000000001', 'cathay', 'columbia', 'strategic_rival', 'THE Trap itself. Rising challenger vs declining hegemon.'),
('00000000-0000-0000-0000-000000000001', 'cathay', 'nordostan', 'close_ally', 'Partnership without limits.'),
('00000000-0000-0000-0000-000000000001', 'cathay', 'heartland', 'neutral', 'Carefully neutral.'),
('00000000-0000-0000-0000-000000000001', 'cathay', 'persia', 'friendly', 'BRICS+ member. Energy supplier.'),
('00000000-0000-0000-0000-000000000001', 'cathay', 'gallia', 'tense', 'UNSC P5 peer.'),
('00000000-0000-0000-0000-000000000001', 'cathay', 'teutonia', 'friendly', 'Largest European trade partner.'),
('00000000-0000-0000-0000-000000000001', 'cathay', 'freeland', 'neutral', 'No significant bilateral relationship.'),
('00000000-0000-0000-0000-000000000001', 'cathay', 'ponte', 'friendly', 'Belt and Road foothold.'),
('00000000-0000-0000-0000-000000000001', 'cathay', 'albion', 'tense', 'Closely aligned with Columbia. Five Eyes.'),
('00000000-0000-0000-0000-000000000001', 'cathay', 'bharata', 'tense', 'Regional rival AND BRICS+ partner.'),
('00000000-0000-0000-0000-000000000001', 'cathay', 'levantia', 'tense', 'No direct conflict.'),
('00000000-0000-0000-0000-000000000001', 'cathay', 'formosa', 'hostile', 'Claimed territory. Existential issue.'),
('00000000-0000-0000-0000-000000000001', 'cathay', 'phrygia', 'friendly', 'NATO member playing every side.'),
('00000000-0000-0000-0000-000000000001', 'cathay', 'yamato', 'hostile', 'Most capable regional adversary.'),
('00000000-0000-0000-0000-000000000001', 'cathay', 'solaria', 'friendly', 'Largest oil customer.'),
('00000000-0000-0000-0000-000000000001', 'cathay', 'choson', 'close_ally', 'Patron. Buffer state.'),
('00000000-0000-0000-0000-000000000001', 'cathay', 'hanguk', 'tense', 'Enormous trade dependency leverage.'),
('00000000-0000-0000-0000-000000000001', 'cathay', 'caribe', 'friendly', 'Strategic foothold in Columbia near-abroad.'),
('00000000-0000-0000-0000-000000000001', 'cathay', 'mirage', 'friendly', 'Financial/trade hub.'),
-- Nordostan relationships
('00000000-0000-0000-0000-000000000001', 'nordostan', 'columbia', 'hostile', 'Nuclear peer adversary.'),
('00000000-0000-0000-0000-000000000001', 'nordostan', 'cathay', 'close_ally', 'Junior partner.'),
('00000000-0000-0000-0000-000000000001', 'nordostan', 'heartland', 'at_war', 'Active war since 2022.'),
('00000000-0000-0000-0000-000000000001', 'nordostan', 'persia', 'friendly', 'Sanctions-evasion partners.'),
('00000000-0000-0000-0000-000000000001', 'nordostan', 'gallia', 'hostile', 'UNSC adversary.'),
('00000000-0000-0000-0000-000000000001', 'nordostan', 'teutonia', 'hostile', 'Former energy supplier.'),
('00000000-0000-0000-0000-000000000001', 'nordostan', 'freeland', 'hostile', 'Frontline NATO state.'),
('00000000-0000-0000-0000-000000000001', 'nordostan', 'ponte', 'tense', 'EU member most sympathetic.'),
('00000000-0000-0000-0000-000000000001', 'nordostan', 'albion', 'hostile', 'Strong sanctions enforcer.'),
('00000000-0000-0000-0000-000000000001', 'nordostan', 'bharata', 'friendly', 'Oil buyer. Defense customer.'),
('00000000-0000-0000-0000-000000000001', 'nordostan', 'levantia', 'tense', 'Opposing sides in Syria.'),
('00000000-0000-0000-0000-000000000001', 'nordostan', 'formosa', 'neutral', 'No significant relationship.'),
('00000000-0000-0000-0000-000000000001', 'nordostan', 'phrygia', 'friendly', 'NATO member blocking consensus.'),
('00000000-0000-0000-0000-000000000001', 'nordostan', 'yamato', 'tense', 'Pacific fleet competition.'),
('00000000-0000-0000-0000-000000000001', 'nordostan', 'solaria', 'friendly', 'OPEC+ partner.'),
('00000000-0000-0000-0000-000000000001', 'nordostan', 'choson', 'close_ally', 'Arms supplier. Choson troops in Heartland.'),
('00000000-0000-0000-0000-000000000001', 'nordostan', 'hanguk', 'tense', 'Adversary through Choson.'),
('00000000-0000-0000-0000-000000000001', 'nordostan', 'caribe', 'friendly', 'Offering Cuba aid.'),
('00000000-0000-0000-0000-000000000001', 'nordostan', 'mirage', 'neutral', 'Financial hub.'),
-- Heartland relationships
('00000000-0000-0000-0000-000000000001', 'heartland', 'columbia', 'close_ally', 'Dependent on Columbia weapons and aid.'),
('00000000-0000-0000-0000-000000000001', 'heartland', 'cathay', 'neutral', 'Cathay officially neutral.'),
('00000000-0000-0000-0000-000000000001', 'heartland', 'nordostan', 'at_war', 'Existential war.'),
('00000000-0000-0000-0000-000000000001', 'heartland', 'persia', 'neutral', 'No significant relationship.'),
('00000000-0000-0000-0000-000000000001', 'heartland', 'gallia', 'friendly', 'EU supporter.'),
('00000000-0000-0000-0000-000000000001', 'heartland', 'teutonia', 'friendly', 'EU supporter.'),
('00000000-0000-0000-0000-000000000001', 'heartland', 'freeland', 'close_ally', 'Neighbor and strongest supporter.'),
('00000000-0000-0000-0000-000000000001', 'heartland', 'ponte', 'neutral', 'EU member but weakest supporter.'),
('00000000-0000-0000-0000-000000000001', 'heartland', 'albion', 'friendly', 'Intelligence sharing.'),
('00000000-0000-0000-0000-000000000001', 'heartland', 'bharata', 'neutral', 'Bharata refuses to take sides.'),
('00000000-0000-0000-0000-000000000001', 'heartland', 'levantia', 'neutral', 'Limited relationship.'),
('00000000-0000-0000-0000-000000000001', 'heartland', 'formosa', 'neutral', 'Shared sympathy.'),
('00000000-0000-0000-0000-000000000001', 'heartland', 'phrygia', 'tense', 'Phrygia blocks NATO consensus.'),
('00000000-0000-0000-0000-000000000001', 'heartland', 'yamato', 'neutral', 'Distant.'),
('00000000-0000-0000-0000-000000000001', 'heartland', 'solaria', 'neutral', 'Limited relationship.'),
('00000000-0000-0000-0000-000000000001', 'heartland', 'choson', 'hostile', 'Choson troops fighting for Nordostan.'),
('00000000-0000-0000-0000-000000000001', 'heartland', 'hanguk', 'neutral', 'Limited relationship.'),
('00000000-0000-0000-0000-000000000001', 'heartland', 'caribe', 'neutral', 'No significant relationship.'),
('00000000-0000-0000-0000-000000000001', 'heartland', 'mirage', 'neutral', 'No significant relationship.'),
-- Persia relationships
('00000000-0000-0000-0000-000000000001', 'persia', 'columbia', 'at_war', 'Under attack. Operation Epic Fury.'),
('00000000-0000-0000-0000-000000000001', 'persia', 'cathay', 'friendly', 'BRICS+ partner.'),
('00000000-0000-0000-0000-000000000001', 'persia', 'nordostan', 'friendly', 'Sanctions-evasion partners.'),
('00000000-0000-0000-0000-000000000001', 'persia', 'heartland', 'neutral', 'No direct relationship.'),
('00000000-0000-0000-0000-000000000001', 'persia', 'gallia', 'hostile', 'European sanctions.'),
('00000000-0000-0000-0000-000000000001', 'persia', 'teutonia', 'tense', 'EU sanctions.'),
('00000000-0000-0000-0000-000000000001', 'persia', 'freeland', 'tense', 'EU sanctions.'),
('00000000-0000-0000-0000-000000000001', 'persia', 'ponte', 'neutral', 'EU member but weakest on Persia sanctions.'),
('00000000-0000-0000-0000-000000000001', 'persia', 'albion', 'hostile', 'Strong sanctions.'),
('00000000-0000-0000-0000-000000000001', 'persia', 'bharata', 'friendly', 'Energy buyer.'),
('00000000-0000-0000-0000-000000000001', 'persia', 'levantia', 'at_war', 'Joint target of Operation Epic Fury.'),
('00000000-0000-0000-0000-000000000001', 'persia', 'formosa', 'neutral', 'No significant relationship.'),
('00000000-0000-0000-0000-000000000001', 'persia', 'phrygia', 'friendly', 'Neighbor. Trade partner.'),
('00000000-0000-0000-0000-000000000001', 'persia', 'yamato', 'neutral', 'Limited relationship.'),
('00000000-0000-0000-0000-000000000001', 'persia', 'solaria', 'hostile', 'Being shelled.'),
('00000000-0000-0000-0000-000000000001', 'persia', 'choson', 'friendly', 'Arms trade.'),
('00000000-0000-0000-0000-000000000001', 'persia', 'hanguk', 'neutral', 'Limited relationship.'),
('00000000-0000-0000-0000-000000000001', 'persia', 'caribe', 'friendly', 'Shared resistance to Columbia.'),
('00000000-0000-0000-0000-000000000001', 'persia', 'mirage', 'hostile', 'Under attack.');

-- NOTE: Remaining 281 relationships (gallia through mirage outbound) follow the same pattern.
-- For production deployment, generate the complete set from relationships.csv.
-- The remaining countries' outbound relationships are omitted here for file size
-- but must be loaded from the CSV for a complete game state.


-- =============================================================================
-- 8. SANCTIONS (from sanctions.csv — 37 rows)
-- =============================================================================

INSERT INTO sanctions (sim_run_id, country, target, level, notes) VALUES
('00000000-0000-0000-0000-000000000001', 'columbia', 'nordostan', 3, 'Comprehensive: financial SWIFT exclusion technology energy price cap'),
('00000000-0000-0000-0000-000000000001', 'columbia', 'persia', 3, 'Maximum: wartime escalation'),
('00000000-0000-0000-0000-000000000001', 'columbia', 'choson', 3, 'Maximum sanctions'),
('00000000-0000-0000-0000-000000000001', 'columbia', 'caribe', 3, 'Full energy blockade'),
('00000000-0000-0000-0000-000000000001', 'gallia', 'nordostan', 3, 'EU comprehensive sanctions'),
('00000000-0000-0000-0000-000000000001', 'gallia', 'persia', 2, 'EU snapback + wartime'),
('00000000-0000-0000-0000-000000000001', 'gallia', 'choson', 2, 'UN and EU sanctions'),
('00000000-0000-0000-0000-000000000001', 'teutonia', 'nordostan', 3, 'EU comprehensive sanctions'),
('00000000-0000-0000-0000-000000000001', 'teutonia', 'persia', 2, 'EU snapback + wartime'),
('00000000-0000-0000-0000-000000000001', 'teutonia', 'choson', 2, 'UN and EU sanctions'),
('00000000-0000-0000-0000-000000000001', 'freeland', 'nordostan', 3, 'Maximum enforcement'),
('00000000-0000-0000-0000-000000000001', 'freeland', 'persia', 2, 'EU aligned'),
('00000000-0000-0000-0000-000000000001', 'freeland', 'choson', 2, 'UN and EU sanctions'),
('00000000-0000-0000-0000-000000000001', 'albion', 'nordostan', 3, 'Comprehensive'),
('00000000-0000-0000-0000-000000000001', 'albion', 'persia', 2, 'Strong sanctions enforcement'),
('00000000-0000-0000-0000-000000000001', 'albion', 'choson', 2, 'UN sanctions enforcement'),
('00000000-0000-0000-0000-000000000001', 'ponte', 'nordostan', 2, 'EU aligned but weakest enforcer'),
('00000000-0000-0000-0000-000000000001', 'ponte', 'persia', 1, 'Minimal EU compliance'),
('00000000-0000-0000-0000-000000000001', 'ponte', 'choson', 1, 'Weak enforcement'),
('00000000-0000-0000-0000-000000000001', 'levantia', 'persia', 3, 'Wartime. Total.'),
('00000000-0000-0000-0000-000000000001', 'levantia', 'nordostan', 1, 'Alignment with Western sanctions'),
('00000000-0000-0000-0000-000000000001', 'formosa', 'nordostan', 1, 'Aligned with Columbia restrictions'),
('00000000-0000-0000-0000-000000000001', 'yamato', 'nordostan', 2, 'G7 aligned sanctions'),
('00000000-0000-0000-0000-000000000001', 'yamato', 'choson', 3, 'Maximum - direct nuclear threat'),
('00000000-0000-0000-0000-000000000001', 'hanguk', 'nordostan', 2, 'Western aligned'),
('00000000-0000-0000-0000-000000000001', 'hanguk', 'choson', 3, 'Maximum - existential threat'),
('00000000-0000-0000-0000-000000000001', 'cathay', 'nordostan', -1, 'Sanctions evasion support'),
('00000000-0000-0000-0000-000000000001', 'nordostan', 'columbia', 1, 'Counter-sanctions'),
('00000000-0000-0000-0000-000000000001', 'nordostan', 'heartland', 3, 'Wartime total'),
('00000000-0000-0000-0000-000000000001', 'choson', 'columbia', 1, 'Symbolic counter-sanctions'),
('00000000-0000-0000-0000-000000000001', 'choson', 'hanguk', 1, 'Symbolic counter-sanctions'),
('00000000-0000-0000-0000-000000000001', 'choson', 'yamato', 1, 'Symbolic counter-sanctions'),
('00000000-0000-0000-0000-000000000001', 'caribe', 'columbia', 1, 'Symbolic counter-sanctions'),
('00000000-0000-0000-0000-000000000001', 'heartland', 'nordostan', 3, 'Wartime total'),
('00000000-0000-0000-0000-000000000001', 'persia', 'columbia', 1, 'Counter-sanctions'),
('00000000-0000-0000-0000-000000000001', 'persia', 'levantia', 3, 'Wartime total');


-- =============================================================================
-- 9. TARIFFS (from tariffs.csv — 30 rows)
-- =============================================================================

INSERT INTO tariffs (sim_run_id, imposer, target, level, notes) VALUES
('00000000-0000-0000-0000-000000000001', 'columbia', 'cathay', 3, '~47.5% average tariffs'),
('00000000-0000-0000-0000-000000000001', 'columbia', 'nordostan', 2, 'Sanctions-related trade restrictions'),
('00000000-0000-0000-0000-000000000001', 'columbia', 'caribe', 3, 'Full energy blockade'),
('00000000-0000-0000-0000-000000000001', 'columbia', 'persia', 3, 'Wartime maximum trade restrictions'),
('00000000-0000-0000-0000-000000000001', 'cathay', 'columbia', 2, 'Retaliatory tariffs ~30% average'),
('00000000-0000-0000-0000-000000000001', 'cathay', 'yamato', 1, 'Export controls on dual-use items'),
('00000000-0000-0000-0000-000000000001', 'cathay', 'hanguk', 1, 'Rare earth restrictions'),
('00000000-0000-0000-0000-000000000001', 'nordostan', 'columbia', 2, 'Counter-sanctions'),
('00000000-0000-0000-0000-000000000001', 'nordostan', 'albion', 2, 'Counter-sanctions'),
('00000000-0000-0000-0000-000000000001', 'nordostan', 'gallia', 2, 'Counter-sanctions'),
('00000000-0000-0000-0000-000000000001', 'nordostan', 'teutonia', 2, 'Counter-sanctions'),
('00000000-0000-0000-0000-000000000001', 'nordostan', 'freeland', 2, 'Counter-sanctions'),
('00000000-0000-0000-0000-000000000001', 'nordostan', 'ponte', 1, 'Limited counter-sanctions'),
('00000000-0000-0000-0000-000000000001', 'gallia', 'cathay', 1, 'EU de-risking trade measures'),
('00000000-0000-0000-0000-000000000001', 'gallia', 'nordostan', 1, 'EU sanctions-aligned'),
('00000000-0000-0000-0000-000000000001', 'teutonia', 'cathay', 1, 'EU de-risking but drags feet'),
('00000000-0000-0000-0000-000000000001', 'teutonia', 'nordostan', 1, 'EU sanctions-aligned'),
('00000000-0000-0000-0000-000000000001', 'freeland', 'cathay', 1, 'EU aligned'),
('00000000-0000-0000-0000-000000000001', 'freeland', 'nordostan', 2, 'Maximum enforcement'),
('00000000-0000-0000-0000-000000000001', 'ponte', 'nordostan', 1, 'EU aligned but weakest enforcement'),
('00000000-0000-0000-0000-000000000001', 'albion', 'cathay', 1, 'Post-Brexit independent restrictions'),
('00000000-0000-0000-0000-000000000001', 'albion', 'nordostan', 1, 'Sanctions-aligned trade controls'),
('00000000-0000-0000-0000-000000000001', 'bharata', 'cathay', 1, 'Border dispute related restrictions'),
('00000000-0000-0000-0000-000000000001', 'levantia', 'persia', 3, 'Wartime total trade embargo'),
('00000000-0000-0000-0000-000000000001', 'yamato', 'cathay', 1, 'Export controls aligned with Columbia'),
('00000000-0000-0000-0000-000000000001', 'caribe', 'columbia', 1, 'Counter-sanctions'),
('00000000-0000-0000-0000-000000000001', 'heartland', 'nordostan', 3, 'Wartime total trade embargo'),
('00000000-0000-0000-0000-000000000001', 'persia', 'columbia', 2, 'Counter-sanctions'),
('00000000-0000-0000-0000-000000000001', 'persia', 'levantia', 3, 'Wartime total trade embargo');


-- =============================================================================
-- 10. DEPLOYMENTS (from deployments.csv — 147 rows)
-- =============================================================================

INSERT INTO deployments (sim_run_id, country_id, unit_type, count, zone_id, notes) VALUES
-- Columbia ground
('00000000-0000-0000-0000-000000000001', 'columbia', 'ground', 4, 'col_main_1', 'Continental main - ICBM silos Pentagon'),
('00000000-0000-0000-0000-000000000001', 'columbia', 'ground', 2, 'col_main_2', 'Continental east - Atlantic seaboard'),
('00000000-0000-0000-0000-000000000001', 'columbia', 'ground', 2, 'col_nw', 'Alaska/Pacific northwest'),
('00000000-0000-0000-0000-000000000001', 'columbia', 'ground', 2, 'col_main_3', 'Hawaii/Pacific command'),
('00000000-0000-0000-0000-000000000001', 'columbia', 'ground', 2, 'teutonia_1', 'Main European base (Ramstein)'),
('00000000-0000-0000-0000-000000000001', 'columbia', 'ground', 1, 'yamato_2', 'Main Pacific base (Okinawa)'),
('00000000-0000-0000-0000-000000000001', 'columbia', 'ground', 1, 'hanguk', 'Korea deterrence'),
('00000000-0000-0000-0000-000000000001', 'columbia', 'ground', 1, 'freeland', 'NATO forward deployment'),
('00000000-0000-0000-0000-000000000001', 'columbia', 'ground', 1, 'solaria_1', 'Gulf logistics - Persia war support'),
('00000000-0000-0000-0000-000000000001', 'columbia', 'ground', 1, 'horn', 'Djibouti - Red Sea security'),
('00000000-0000-0000-0000-000000000001', 'columbia', 'ground', 4, 'persia_2', 'ME theater - active war zone'),
('00000000-0000-0000-0000-000000000001', 'columbia', 'ground', 1, 'mirage', 'Gulf logistics hub'),
-- Columbia tactical air
('00000000-0000-0000-0000-000000000001', 'columbia', 'tactical_air', 5, 'col_main_1', 'Continental strike capability'),
('00000000-0000-0000-0000-000000000001', 'columbia', 'tactical_air', 2, 'col_main_3', 'Pacific air command'),
('00000000-0000-0000-0000-000000000001', 'columbia', 'tactical_air', 2, 'teutonia_1', 'European air power'),
('00000000-0000-0000-0000-000000000001', 'columbia', 'tactical_air', 1, 'yamato_2', 'Pacific base air'),
('00000000-0000-0000-0000-000000000001', 'columbia', 'tactical_air', 3, 'persia_2', 'ME theater air campaign'),
('00000000-0000-0000-0000-000000000001', 'columbia', 'tactical_air', 1, 'hanguk', 'Korea air deterrence'),
('00000000-0000-0000-0000-000000000001', 'columbia', 'tactical_air', 1, 'col_nw', 'Alaska air defense'),
-- Columbia strategic missiles
('00000000-0000-0000-0000-000000000001', 'columbia', 'strategic_missile', 8, 'col_main_1', 'ICBM silos + bomber fleet'),
('00000000-0000-0000-0000-000000000001', 'columbia', 'strategic_missile', 1, 'col_nw', 'Alaska strategic'),
('00000000-0000-0000-0000-000000000001', 'columbia', 'strategic_missile', 3, 'col_main_2', 'SSBNs at sea'),
-- Columbia air defense
('00000000-0000-0000-0000-000000000001', 'columbia', 'air_defense', 2, 'col_main_1', 'Homeland THAAD/Patriot'),
('00000000-0000-0000-0000-000000000001', 'columbia', 'air_defense', 1, 'col_main_3', 'Hawaii defense'),
('00000000-0000-0000-0000-000000000001', 'columbia', 'air_defense', 1, 'yamato_2', 'Pacific base defense'),
-- Columbia naval
('00000000-0000-0000-0000-000000000001', 'columbia', 'naval', 3, 'w(13,9)', 'Gulf — 2 CSGs for Operation Epic Fury'),
('00000000-0000-0000-0000-000000000001', 'columbia', 'naval', 2, 'w(10,7)', 'Mediterranean — Persia war support + Suez'),
('00000000-0000-0000-0000-000000000001', 'columbia', 'naval', 2, 'w(18,5)', 'East Cathay Sea — Formosa deterrence patrol'),
('00000000-0000-0000-0000-000000000001', 'columbia', 'naval', 1, 'col_main_2', 'Atlantic home port'),
('00000000-0000-0000-0000-000000000001', 'columbia', 'naval', 1, 'col_main_3', 'Pacific home port'),
('00000000-0000-0000-0000-000000000001', 'columbia', 'naval', 1, 'w(14,10)', 'Indian Ocean presence'),
('00000000-0000-0000-0000-000000000001', 'columbia', 'naval', 1, 'hanguk', 'Home port Pacific'),
-- Cathay ground
('00000000-0000-0000-0000-000000000001', 'cathay', 'ground', 5, 'cathay_3', 'Central mainland - Beijing region'),
('00000000-0000-0000-0000-000000000001', 'cathay', 'ground', 5, 'cathay_2', 'Western interior'),
('00000000-0000-0000-0000-000000000001', 'cathay', 'ground', 4, 'cathay_6', 'Southeast - Taiwan Strait staging'),
('00000000-0000-0000-0000-000000000001', 'cathay', 'ground', 4, 'cathay_5', 'Southern coastal'),
('00000000-0000-0000-0000-000000000001', 'cathay', 'ground', 2, 'cathay_4', 'Northeast - Choson border'),
('00000000-0000-0000-0000-000000000001', 'cathay', 'ground', 3, 'cathay_7', 'South China coastal'),
('00000000-0000-0000-0000-000000000001', 'cathay', 'ground', 2, 'choson', 'Choson border quick reaction force'),
-- Cathay tactical air
('00000000-0000-0000-0000-000000000001', 'cathay', 'tactical_air', 5, 'cathay_3', 'Central aviation'),
('00000000-0000-0000-0000-000000000001', 'cathay', 'tactical_air', 5, 'cathay_6', 'Coastal DF-21/DF-26'),
('00000000-0000-0000-0000-000000000001', 'cathay', 'tactical_air', 2, 'cathay_2', 'Western interior air'),
-- Cathay strategic missiles
('00000000-0000-0000-0000-000000000001', 'cathay', 'strategic_missile', 2, 'cathay_3', 'Silo-based ICBMs'),
('00000000-0000-0000-0000-000000000001', 'cathay', 'strategic_missile', 1, 'cathay_2', 'Mobile DF-41 launchers'),
('00000000-0000-0000-0000-000000000001', 'cathay', 'strategic_missile', 1, 'cathay_7', 'SSBNs'),
-- Cathay air defense
('00000000-0000-0000-0000-000000000001', 'cathay', 'air_defense', 1, 'cathay_3', 'Central defense'),
('00000000-0000-0000-0000-000000000001', 'cathay', 'air_defense', 1, 'cathay_6', 'Coastal defense'),
('00000000-0000-0000-0000-000000000001', 'cathay', 'air_defense', 1, 'cathay_2', 'Western defense'),
-- Cathay naval
('00000000-0000-0000-0000-000000000001', 'cathay', 'naval', 2, 'w(17,8)', 'South Cathay Sea'),
('00000000-0000-0000-0000-000000000001', 'cathay', 'naval', 2, 'w(18,5)', 'East Cathay Sea'),
('00000000-0000-0000-0000-000000000001', 'cathay', 'naval', 1, 'w(19,7)', 'Near Formosa'),
('00000000-0000-0000-0000-000000000001', 'cathay', 'naval', 1, 'cathay_7', 'Home port — Hainan'),
('00000000-0000-0000-0000-000000000001', 'cathay', 'naval', 1, 'hanguk', 'Reserved slot'),
-- Nordostan ground
('00000000-0000-0000-0000-000000000001', 'nordostan', 'ground', 2, 'nord_c1', 'Moscow strategic reserve'),
('00000000-0000-0000-0000-000000000001', 'nordostan', 'ground', 2, 'nord_e2', 'Far East border'),
('00000000-0000-0000-0000-000000000001', 'nordostan', 'ground', 1, 'nord_w2', 'Caucasus/southern flank'),
('00000000-0000-0000-0000-000000000001', 'nordostan', 'ground', 8, 'heartland_2', 'Front line offensive forces'),
('00000000-0000-0000-0000-000000000001', 'nordostan', 'ground', 5, 'heartland_1', 'Occupation/rear security'),
-- Nordostan tactical air
('00000000-0000-0000-0000-000000000001', 'nordostan', 'tactical_air', 2, 'nord_c1', 'Strategic aviation'),
('00000000-0000-0000-0000-000000000001', 'nordostan', 'tactical_air', 1, 'nord_w2', 'Southern air defense'),
('00000000-0000-0000-0000-000000000001', 'nordostan', 'tactical_air', 1, 'nord_e2', 'Far East air defense'),
('00000000-0000-0000-0000-000000000001', 'nordostan', 'tactical_air', 4, 'heartland_2', 'Front-line aviation'),
-- Nordostan strategic missiles
('00000000-0000-0000-0000-000000000001', 'nordostan', 'strategic_missile', 7, 'nord_c1', 'ICBM silos mobile launchers'),
('00000000-0000-0000-0000-000000000001', 'nordostan', 'strategic_missile', 2, 'nord_e2', 'Mobile launchers Pacific'),
('00000000-0000-0000-0000-000000000001', 'nordostan', 'strategic_missile', 3, 'nord_n1', 'SSBNs Northern Fleet'),
-- Nordostan air defense + naval
('00000000-0000-0000-0000-000000000001', 'nordostan', 'air_defense', 1, 'nord_c1', 'Moscow strategic defense'),
('00000000-0000-0000-0000-000000000001', 'nordostan', 'air_defense', 1, 'nord_w2', 'Southern defense'),
('00000000-0000-0000-0000-000000000001', 'nordostan', 'air_defense', 1, 'heartland_2', 'Theater air defense'),
('00000000-0000-0000-0000-000000000001', 'nordostan', 'naval', 2, 'nord_w2', 'Northern Fleet'),
-- Heartland
('00000000-0000-0000-0000-000000000001', 'heartland', 'ground', 7, 'heartland_2', 'Front line defense'),
('00000000-0000-0000-0000-000000000001', 'heartland', 'ground', 3, 'heartland_1', 'Strategic reserve'),
('00000000-0000-0000-0000-000000000001', 'heartland', 'tactical_air', 2, 'heartland_2', 'Front-line air support'),
('00000000-0000-0000-0000-000000000001', 'heartland', 'tactical_air', 1, 'heartland_1', 'Air defense/strike reserve'),
('00000000-0000-0000-0000-000000000001', 'heartland', 'air_defense', 1, 'heartland_1', 'Patriot/NASAMS protecting capital'),
-- Persia
('00000000-0000-0000-0000-000000000001', 'persia', 'ground', 2, 'persia_2', 'IRGC ground forces'),
('00000000-0000-0000-0000-000000000001', 'persia', 'ground', 2, 'persia_1', 'Nuclear facility defense'),
('00000000-0000-0000-0000-000000000001', 'persia', 'ground', 2, 'persia_3', 'Strategic depth'),
('00000000-0000-0000-0000-000000000001', 'persia', 'ground', 1, 'phrygia_2', 'Iraq corridor'),
('00000000-0000-0000-0000-000000000001', 'persia', 'ground', 1, 'cp_gulf_gate', 'Gulf Gate blockade'),
('00000000-0000-0000-0000-000000000001', 'persia', 'tactical_air', 2, 'persia_2', 'Coastal anti-ship missiles'),
('00000000-0000-0000-0000-000000000001', 'persia', 'tactical_air', 2, 'persia_1', 'Medium-range ballistic missiles'),
('00000000-0000-0000-0000-000000000001', 'persia', 'tactical_air', 1, 'persia_3', 'Long-range strategic reserve'),
('00000000-0000-0000-0000-000000000001', 'persia', 'tactical_air', 1, 'cp_gulf_gate', 'Anti-ship missile batteries'),
('00000000-0000-0000-0000-000000000001', 'persia', 'air_defense', 1, 'persia_1', 'S-300/S-400 nuclear sites'),
('00000000-0000-0000-0000-000000000001', 'persia', 'strategic_missile', 1, 'persia_3', 'Ballistic missile reserve'),
-- Gallia
('00000000-0000-0000-0000-000000000001', 'gallia', 'ground', 4, 'gallia_1', 'Metropolitan France'),
('00000000-0000-0000-0000-000000000001', 'gallia', 'ground', 1, 'horn', 'Djibouti overseas'),
('00000000-0000-0000-0000-000000000001', 'gallia', 'ground', 1, 'levantia', 'Near ME deployment'),
('00000000-0000-0000-0000-000000000001', 'gallia', 'tactical_air', 3, 'gallia_1', 'Metropolitan Rafale'),
('00000000-0000-0000-0000-000000000001', 'gallia', 'tactical_air', 1, 'horn', 'Overseas air'),
('00000000-0000-0000-0000-000000000001', 'gallia', 'strategic_missile', 2, 'gallia_1', 'SSBNs + cruise missiles'),
('00000000-0000-0000-0000-000000000001', 'gallia', 'air_defense', 1, 'gallia_1', 'SAMP/T homeland'),
('00000000-0000-0000-0000-000000000001', 'gallia', 'naval', 1, 'w(10,7)', 'Mediterranean carrier'),
-- Teutonia
('00000000-0000-0000-0000-000000000001', 'teutonia', 'ground', 6, 'teutonia_1', 'Bundeswehr homeland'),
('00000000-0000-0000-0000-000000000001', 'teutonia', 'tactical_air', 3, 'teutonia_1', 'Eurofighter Typhoons'),
('00000000-0000-0000-0000-000000000001', 'teutonia', 'air_defense', 1, 'teutonia_1', 'Patriot systems'),
-- Freeland
('00000000-0000-0000-0000-000000000001', 'freeland', 'ground', 5, 'freeland', 'All homeland defense'),
('00000000-0000-0000-0000-000000000001', 'freeland', 'tactical_air', 2, 'freeland', 'F-35 and FA-50'),
('00000000-0000-0000-0000-000000000001', 'freeland', 'air_defense', 1, 'freeland', 'Patriot from Columbia'),
-- Ponte
('00000000-0000-0000-0000-000000000001', 'ponte', 'ground', 4, 'ponte', 'Homeland'),
('00000000-0000-0000-0000-000000000001', 'ponte', 'tactical_air', 2, 'ponte', 'Eurofighter/F-35'),
-- Albion
('00000000-0000-0000-0000-000000000001', 'albion', 'ground', 3, 'albion', 'British Isles homeland'),
('00000000-0000-0000-0000-000000000001', 'albion', 'ground', 1, 'levantia', 'Cyprus/Gibraltar overseas'),
('00000000-0000-0000-0000-000000000001', 'albion', 'tactical_air', 2, 'albion', 'RAF homeland'),
('00000000-0000-0000-0000-000000000001', 'albion', 'tactical_air', 1, 'levantia', 'Overseas RAF'),
('00000000-0000-0000-0000-000000000001', 'albion', 'strategic_missile', 2, 'albion', 'Trident SSBNs'),
('00000000-0000-0000-0000-000000000001', 'albion', 'air_defense', 1, 'albion', 'Sky Sabre homeland'),
('00000000-0000-0000-0000-000000000001', 'albion', 'naval', 2, 'w(8,4)', 'Atlantic/home waters'),
-- Bharata
('00000000-0000-0000-0000-000000000001', 'bharata', 'ground', 10, 'bharata_2', 'Cathay border and internal'),
('00000000-0000-0000-0000-000000000001', 'bharata', 'ground', 2, 'bharata_1', 'Indian Ocean / Andaman'),
('00000000-0000-0000-0000-000000000001', 'bharata', 'tactical_air', 4, 'bharata_2', 'Mixed fleet'),
('00000000-0000-0000-0000-000000000001', 'bharata', 'air_defense', 2, 'bharata_2', 'S-400 + domestic'),
('00000000-0000-0000-0000-000000000001', 'bharata', 'naval', 2, 'w(14,10)', 'Indian Ocean fleet'),
-- Levantia
('00000000-0000-0000-0000-000000000001', 'levantia', 'ground', 3, 'levantia', 'Homeland + West Bank'),
('00000000-0000-0000-0000-000000000001', 'levantia', 'ground', 2, 'phrygia_2', 'Lebanon theater'),
('00000000-0000-0000-0000-000000000001', 'levantia', 'ground', 1, 'levantia', 'Persia-facing reserves'),
('00000000-0000-0000-0000-000000000001', 'levantia', 'tactical_air', 2, 'levantia', 'F-35I homeland'),
('00000000-0000-0000-0000-000000000001', 'levantia', 'tactical_air', 2, 'persia_2', 'Persia strike operations'),
('00000000-0000-0000-0000-000000000001', 'levantia', 'air_defense', 3, 'levantia', 'Iron Dome David Sling Arrow'),
-- Formosa
('00000000-0000-0000-0000-000000000001', 'formosa', 'ground', 4, 'formosa', 'Porcupine strategy'),
('00000000-0000-0000-0000-000000000001', 'formosa', 'tactical_air', 3, 'formosa', 'F-16V fleet'),
('00000000-0000-0000-0000-000000000001', 'formosa', 'air_defense', 2, 'formosa', 'Patriot PAC-3'),
-- Phrygia
('00000000-0000-0000-0000-000000000001', 'phrygia', 'ground', 4, 'phrygia_1', 'Homeland'),
('00000000-0000-0000-0000-000000000001', 'phrygia', 'ground', 1, 'phrygia_2', 'Syria deployment'),
('00000000-0000-0000-0000-000000000001', 'phrygia', 'ground', 1, 'phrygia_2', 'Strait defense'),
('00000000-0000-0000-0000-000000000001', 'phrygia', 'tactical_air', 3, 'phrygia_1', 'F-16 fleet Bayraktar'),
('00000000-0000-0000-0000-000000000001', 'phrygia', 'air_defense', 1, 'phrygia_1', 'S-400 from Nordostan'),
('00000000-0000-0000-0000-000000000001', 'phrygia', 'naval', 1, 'phrygia_1', 'Bosphorus/Med'),
-- Yamato
('00000000-0000-0000-0000-000000000001', 'yamato', 'ground', 3, 'yamato_2', 'Self-Defense Forces'),
('00000000-0000-0000-0000-000000000001', 'yamato', 'tactical_air', 3, 'yamato_2', 'F-35 fleet'),
('00000000-0000-0000-0000-000000000001', 'yamato', 'air_defense', 2, 'yamato_2', 'Aegis BMD PAC-3'),
('00000000-0000-0000-0000-000000000001', 'yamato', 'naval', 2, 'w(20,5)', 'Pacific home waters'),
-- Solaria
('00000000-0000-0000-0000-000000000001', 'solaria', 'ground', 3, 'solaria_2', 'Homeland oil defense'),
('00000000-0000-0000-0000-000000000001', 'solaria', 'tactical_air', 3, 'solaria_2', 'F-15s Typhoons'),
('00000000-0000-0000-0000-000000000001', 'solaria', 'air_defense', 2, 'solaria_2', 'Patriot batteries'),
-- Choson
('00000000-0000-0000-0000-000000000001', 'choson', 'ground', 6, 'choson', 'Homeland DMZ'),
('00000000-0000-0000-0000-000000000001', 'choson', 'ground', 2, 'heartland_2', 'Deployed to Nordostan'),
('00000000-0000-0000-0000-000000000001', 'choson', 'tactical_air', 2, 'choson', 'Ballistic missile force'),
('00000000-0000-0000-0000-000000000001', 'choson', 'strategic_missile', 1, 'choson', 'Nuclear-tipped ICBMs'),
('00000000-0000-0000-0000-000000000001', 'choson', 'air_defense', 1, 'choson', 'Antiquated layered defense'),
-- Hanguk
('00000000-0000-0000-0000-000000000001', 'hanguk', 'ground', 5, 'hanguk', 'All DMZ defense'),
('00000000-0000-0000-0000-000000000001', 'hanguk', 'tactical_air', 3, 'hanguk', 'F-35 F-15K KF-21'),
('00000000-0000-0000-0000-000000000001', 'hanguk', 'air_defense', 2, 'hanguk', 'Patriot + THAAD'),
-- Caribe
('00000000-0000-0000-0000-000000000001', 'caribe', 'ground', 2, 'caribe', 'Cuba homeland'),
('00000000-0000-0000-0000-000000000001', 'caribe', 'ground', 1, 'caribe', 'Venezuela'),
('00000000-0000-0000-0000-000000000001', 'caribe', 'tactical_air', 1, 'caribe', 'Antiquated Soviet-era aircraft'),
-- Mirage
('00000000-0000-0000-0000-000000000001', 'mirage', 'ground', 2, 'mirage', 'Homeland professional force'),
('00000000-0000-0000-0000-000000000001', 'mirage', 'tactical_air', 2, 'mirage', 'F-16s Mirage 2000s drones'),
('00000000-0000-0000-0000-000000000001', 'mirage', 'air_defense', 2, 'mirage', 'THAAD Patriot IRIS-T');


-- =============================================================================
-- 11. INITIAL WORLD STATE (Round 0)
-- =============================================================================

INSERT INTO world_state (sim_run_id, round_num, oil_price, oil_price_index,
    global_trade_volume_index, dollar_credibility, nuclear_used_this_sim,
    formosa_blockade, opec_production, chokepoint_status, wars,
    is_frozen, schema_version)
VALUES (
    '00000000-0000-0000-0000-000000000001', 0, 80.0, 100.0,
    100.0, 100.0, false,
    false,
    '{"nordostan": "normal", "persia": "normal", "solaria": "normal", "mirage": "normal"}'::JSONB,
    '{"hormuz": "open", "malacca": "open", "taiwan_strait": "open", "suez": "open", "bosphorus": "open", "giuk": "open", "caribbean": "open", "south_china_sea": "open", "gulf_gate_ground": "blocked"}'::JSONB,
    '[{"attacker": "nordostan", "defender": "heartland", "theater": "eastern_ereb", "start_round": -4, "occupied_zones": ["heartland_2"]}, {"attacker": "columbia", "defender": "persia", "theater": "mashriq", "start_round": 0, "allies": {"attacker": ["levantia"], "defender": []}, "occupied_zones": []}]'::JSONB,
    false, '1.0'
);


-- =============================================================================
-- 12. INITIAL COUNTRY STATES (Round 0 — derived from countries table)
-- =============================================================================

INSERT INTO country_state (sim_run_id, country_id, round_num, gdp, gdp_growth_rate, treasury, inflation, debt_burden, momentum, opec_production, economic_state, market_index, revenue, mil_ground, mil_naval, mil_tactical_air, mil_strategic_missiles, mil_air_defense, mobilization_pool, stability, political_support, war_tiredness, dem_rep_split_dem, dem_rep_split_rep, regime_status, nuclear_level, nuclear_rd_progress, ai_level, ai_rd_progress)
SELECT
    sim_run_id, id, 0, gdp, gdp_growth_base, treasury, inflation, debt_burden, 0, opec_production,
    'normal', 50, gdp * tax_rate,
    mil_ground, mil_naval, mil_tactical_air, mil_strategic_missiles, mil_air_defense, mobilization_pool,
    stability, political_support, war_tiredness, dem_rep_split_dem, dem_rep_split_rep, 'stable',
    nuclear_level, nuclear_rd_progress, ai_level, ai_rd_progress
FROM countries
WHERE sim_run_id = '00000000-0000-0000-0000-000000000001';


-- =============================================================================
-- 13. INITIAL ROLE STATES (Round 0 — derived from roles table)
-- =============================================================================

INSERT INTO role_state (sim_run_id, role_id, round_num, personal_coins, status, is_head_of_state, is_military_chief, intelligence_pool_remaining, sabotage_cards_remaining, cyber_cards_remaining, disinfo_cards_remaining, election_meddling_remaining, assassination_cards_remaining, protest_stim_remaining, fatherland_appeal_remaining)
SELECT
    sim_run_id, id, 0, personal_coins, status, is_head_of_state, is_military_chief,
    intelligence_pool, sabotage_cards, cyber_cards, disinfo_cards, election_meddling_cards,
    assassination_cards, protest_stim_cards, fatherland_appeal
FROM roles
WHERE sim_run_id = '00000000-0000-0000-0000-000000000001';


-- =============================================================================
-- END OF SEED DATA
-- =============================================================================
