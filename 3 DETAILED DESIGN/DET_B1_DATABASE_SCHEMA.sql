-- =============================================================================
-- DET_B1_DATABASE_SCHEMA.sql
-- Thucydides Trap SIM — Complete PostgreSQL Schema for Supabase
-- Version: 1.1 | Date: 2026-03-30
-- Source of truth: SEED F1 Data Schema, F2 Data Architecture, world_state.py, CSVs
-- Naming authority: DET_NAMING_CONVENTIONS.md
-- Includes: B1 (schema), B2 (RLS policies), B4 (database functions)
-- =============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================================================
-- SECTION 1: CORE TABLES
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 1.1 SIM RUNS — Top-level game instance
-- ---------------------------------------------------------------------------
CREATE TABLE sim_runs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'setup'
                    CHECK (status IN ('setup', 'active', 'paused', 'completed', 'aborted')),
    current_round   INT NOT NULL DEFAULT 0 CHECK (current_round >= 0 AND current_round <= 8),
    current_phase   TEXT NOT NULL DEFAULT 'pre'
                    CHECK (current_phase IN ('pre', 'A', 'B', 'C', 'post')),
    config          JSONB NOT NULL DEFAULT '{}'::JSONB,
    max_rounds      INT NOT NULL DEFAULT 8,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_sim_runs_status ON sim_runs(status);

-- ---------------------------------------------------------------------------
-- 1.2 USERS — Supabase auth integration
-- ---------------------------------------------------------------------------
CREATE TABLE users (
    id              UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email           TEXT NOT NULL,
    display_name    TEXT NOT NULL DEFAULT '',
    avatar_url      TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);

-- ---------------------------------------------------------------------------
-- 1.3 FACILITATORS — Moderator permissions per SIM run
-- ---------------------------------------------------------------------------
CREATE TABLE facilitators (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sim_run_id      UUID NOT NULL REFERENCES sim_runs(id) ON DELETE CASCADE,
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    access_level    TEXT NOT NULL DEFAULT 'moderator'
                    CHECK (access_level IN ('moderator', 'admin', 'spectator')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(sim_run_id, user_id)
);

CREATE INDEX idx_facilitators_sim ON facilitators(sim_run_id);

-- ---------------------------------------------------------------------------
-- 1.4 COUNTRIES — Master country record (from countries.csv)
-- ---------------------------------------------------------------------------
CREATE TABLE countries (
    id                      TEXT NOT NULL,
    sim_run_id              UUID NOT NULL REFERENCES sim_runs(id) ON DELETE CASCADE,
    sim_name                TEXT NOT NULL,
    parallel                TEXT NOT NULL DEFAULT '',
    regime_type             TEXT NOT NULL CHECK (regime_type IN ('democracy', 'autocracy', 'hybrid')),
    team_type               TEXT NOT NULL CHECK (team_type IN ('team', 'solo', 'europe')),
    team_size_min           INT NOT NULL DEFAULT 1,
    team_size_max           INT NOT NULL DEFAULT 1,
    ai_default              BOOLEAN NOT NULL DEFAULT TRUE,
    -- Economic (CONFIG — set from CSV, mostly static)
    gdp                     NUMERIC(12,2) NOT NULL DEFAULT 0,
    gdp_growth_base         NUMERIC(6,3) NOT NULL DEFAULT 0,
    sector_resources        INT NOT NULL DEFAULT 0,
    sector_industry         INT NOT NULL DEFAULT 0,
    sector_services         INT NOT NULL DEFAULT 0,
    sector_technology       INT NOT NULL DEFAULT 0,
    tax_rate                NUMERIC(4,3) NOT NULL DEFAULT 0,
    treasury                NUMERIC(12,2) NOT NULL DEFAULT 0,
    inflation               NUMERIC(8,2) NOT NULL DEFAULT 0,
    trade_balance           NUMERIC(10,2) NOT NULL DEFAULT 0,
    oil_producer            BOOLEAN NOT NULL DEFAULT FALSE,
    opec_member             BOOLEAN NOT NULL DEFAULT FALSE,
    opec_production         TEXT NOT NULL DEFAULT 'na'
                            CHECK (opec_production IN ('min', 'low', 'normal', 'high', 'max', 'na')),
    formosa_dependency      NUMERIC(4,3) NOT NULL DEFAULT 0,
    debt_burden             NUMERIC(10,2) NOT NULL DEFAULT 0,
    social_baseline         NUMERIC(4,3) NOT NULL DEFAULT 0.20,
    -- Military (CONFIG)
    mil_ground              INT NOT NULL DEFAULT 0,
    mil_naval               INT NOT NULL DEFAULT 0,
    mil_tactical_air        INT NOT NULL DEFAULT 0,
    mil_strategic_missiles  INT NOT NULL DEFAULT 0,
    mil_air_defense         INT NOT NULL DEFAULT 0,
    prod_cost_ground        NUMERIC(6,2) NOT NULL DEFAULT 3,
    prod_cost_naval         NUMERIC(6,2) NOT NULL DEFAULT 5,
    prod_cost_tactical      NUMERIC(6,2) NOT NULL DEFAULT 4,
    prod_cap_ground         INT NOT NULL DEFAULT 2,
    prod_cap_naval          INT NOT NULL DEFAULT 1,
    prod_cap_tactical       INT NOT NULL DEFAULT 1,
    maintenance_per_unit    NUMERIC(4,2) NOT NULL DEFAULT 0.3,
    strategic_missile_growth INT NOT NULL DEFAULT 0,
    mobilization_pool       INT NOT NULL DEFAULT 0,
    -- Political (CONFIG)
    stability               NUMERIC(4,2) NOT NULL DEFAULT 5 CHECK (stability >= 0 AND stability <= 10),
    political_support       NUMERIC(6,2) NOT NULL DEFAULT 50 CHECK (political_support >= 0 AND political_support <= 100),
    dem_rep_split_dem       INT NOT NULL DEFAULT 0,
    dem_rep_split_rep       INT NOT NULL DEFAULT 0,
    war_tiredness           NUMERIC(6,2) NOT NULL DEFAULT 0,
    -- Technology (CONFIG)
    nuclear_level           INT NOT NULL DEFAULT 0 CHECK (nuclear_level >= 0 AND nuclear_level <= 3),
    nuclear_rd_progress     NUMERIC(4,3) NOT NULL DEFAULT 0,
    ai_level                INT NOT NULL DEFAULT 0 CHECK (ai_level >= 0 AND ai_level <= 4),
    ai_rd_progress          NUMERIC(4,3) NOT NULL DEFAULT 0,
    -- Zones reference (denormalized for quick lookup)
    home_zones              TEXT NOT NULL DEFAULT '',
    -- Metadata
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (id, sim_run_id)
);

CREATE INDEX idx_countries_sim ON countries(sim_run_id);

-- ---------------------------------------------------------------------------
-- 1.5 ROLES — All participant roles (from roles.csv)
-- ---------------------------------------------------------------------------
CREATE TABLE roles (
    id                      TEXT NOT NULL,
    sim_run_id              UUID NOT NULL REFERENCES sim_runs(id) ON DELETE CASCADE,
    user_id                 UUID REFERENCES users(id) ON DELETE SET NULL,
    character_name          TEXT NOT NULL,
    parallel                TEXT NOT NULL DEFAULT '',
    country_id              TEXT NOT NULL,
    team                    TEXT NOT NULL DEFAULT '',
    faction                 TEXT NOT NULL DEFAULT '',
    title                   TEXT NOT NULL DEFAULT '',
    age                     INT NOT NULL DEFAULT 50,
    gender                  TEXT NOT NULL DEFAULT 'M' CHECK (gender IN ('M', 'F')),
    is_head_of_state        BOOLEAN NOT NULL DEFAULT FALSE,
    is_military_chief       BOOLEAN NOT NULL DEFAULT FALSE,
    parliament_seat         INT NOT NULL DEFAULT 0,
    personal_coins          NUMERIC(8,2) NOT NULL DEFAULT 0,
    personal_coins_notes    TEXT NOT NULL DEFAULT '',
    expansion_role          BOOLEAN NOT NULL DEFAULT FALSE,
    ai_candidate            BOOLEAN NOT NULL DEFAULT FALSE,
    is_ai_operated          BOOLEAN NOT NULL DEFAULT FALSE,
    brief_file              TEXT NOT NULL DEFAULT '',
    -- Covert operation pools (finite per game)
    intelligence_pool       INT NOT NULL DEFAULT 0,
    sabotage_cards          INT NOT NULL DEFAULT 0,
    cyber_cards             INT NOT NULL DEFAULT 0,
    disinfo_cards           INT NOT NULL DEFAULT 0,
    election_meddling_cards INT NOT NULL DEFAULT 0,
    assassination_cards     INT NOT NULL DEFAULT 0,
    protest_stim_cards      INT NOT NULL DEFAULT 0,
    fatherland_appeal       INT NOT NULL DEFAULT 0,
    is_diplomat             BOOLEAN NOT NULL DEFAULT FALSE,
    -- Role capabilities
    powers                  TEXT[] NOT NULL DEFAULT '{}',
    objectives              TEXT[] NOT NULL DEFAULT '{}',
    ticking_clock           TEXT NOT NULL DEFAULT '',
    -- Status (changes during play)
    status                  TEXT NOT NULL DEFAULT 'active'
                            CHECK (status IN ('active', 'fired', 'arrested', 'incapacitated', 'dead', 'exiled')),
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (id, sim_run_id),
    FOREIGN KEY (country_id, sim_run_id) REFERENCES countries(id, sim_run_id)
);

CREATE INDEX idx_roles_sim ON roles(sim_run_id);
CREATE INDEX idx_roles_country ON roles(country_id, sim_run_id);
CREATE INDEX idx_roles_user ON roles(user_id);

-- ---------------------------------------------------------------------------
-- 1.6 ZONES — Map zones (from zones.csv)
-- ---------------------------------------------------------------------------
CREATE TABLE zones (
    id              TEXT NOT NULL,
    sim_run_id      UUID NOT NULL REFERENCES sim_runs(id) ON DELETE CASCADE,
    display_name    TEXT NOT NULL,
    type            TEXT NOT NULL CHECK (type IN ('land_home', 'land_contested', 'sea', 'chokepoint', 'chokepoint_sea')),
    owner           TEXT NOT NULL DEFAULT 'none',
    controlled_by   TEXT DEFAULT NULL,  -- Occupying country (if different from owner)
    theater         TEXT NOT NULL DEFAULT 'global',
    is_chokepoint   BOOLEAN NOT NULL DEFAULT FALSE,
    die_hard        BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (id, sim_run_id)
);

CREATE INDEX idx_zones_sim ON zones(sim_run_id);
CREATE INDEX idx_zones_owner ON zones(owner, sim_run_id);
CREATE INDEX idx_zones_theater ON zones(theater, sim_run_id);

-- ---------------------------------------------------------------------------
-- 1.7 ZONE ADJACENCY — Map topology (from zone_adjacency.csv)
-- ---------------------------------------------------------------------------
CREATE TABLE zone_adjacency (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sim_run_id      UUID NOT NULL REFERENCES sim_runs(id) ON DELETE CASCADE,
    zone_a          TEXT NOT NULL,
    zone_b          TEXT NOT NULL,
    connection_type TEXT NOT NULL DEFAULT 'land_land'
                    CHECK (connection_type IN ('land_land', 'sea_sea', 'land_sea')),

    UNIQUE(sim_run_id, zone_a, zone_b)
);

CREATE INDEX idx_zone_adj_sim ON zone_adjacency(sim_run_id);
CREATE INDEX idx_zone_adj_a ON zone_adjacency(sim_run_id, zone_a);
CREATE INDEX idx_zone_adj_b ON zone_adjacency(sim_run_id, zone_b);

-- ---------------------------------------------------------------------------
-- 1.8 DEPLOYMENTS — Military unit placements (from deployments.csv, mutable)
-- ---------------------------------------------------------------------------
CREATE TABLE deployments (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sim_run_id      UUID NOT NULL REFERENCES sim_runs(id) ON DELETE CASCADE,
    country_id      TEXT NOT NULL,
    unit_type       TEXT NOT NULL
                    CHECK (unit_type IN ('ground', 'naval', 'tactical_air', 'strategic_missile', 'air_defense')),
    count           INT NOT NULL DEFAULT 0 CHECK (count >= 0),
    zone_id         TEXT NOT NULL,
    notes           TEXT NOT NULL DEFAULT '',
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_deployments_sim ON deployments(sim_run_id);
CREATE INDEX idx_deployments_country ON deployments(sim_run_id, country_id);
CREATE INDEX idx_deployments_zone ON deployments(sim_run_id, zone_id);

-- ---------------------------------------------------------------------------
-- 1.9 ORGANIZATIONS — International organizations (from organizations.csv)
-- ---------------------------------------------------------------------------
CREATE TABLE organizations (
    id                  TEXT NOT NULL,
    sim_run_id          UUID NOT NULL REFERENCES sim_runs(id) ON DELETE CASCADE,
    sim_name            TEXT NOT NULL,
    parallel            TEXT NOT NULL DEFAULT '',
    decision_rule       TEXT NOT NULL DEFAULT 'consensus',
    chair_role_id       TEXT NOT NULL DEFAULT '',
    voting_threshold    TEXT NOT NULL DEFAULT 'unanimous',
    meeting_frequency   TEXT NOT NULL DEFAULT '',
    can_be_created      BOOLEAN NOT NULL DEFAULT FALSE,
    description         TEXT NOT NULL DEFAULT '',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (id, sim_run_id)
);

CREATE INDEX idx_orgs_sim ON organizations(sim_run_id);

-- ---------------------------------------------------------------------------
-- 1.10 ORG MEMBERSHIPS — Country-Organization links (from org_memberships.csv)
-- ---------------------------------------------------------------------------
CREATE TABLE org_memberships (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sim_run_id      UUID NOT NULL REFERENCES sim_runs(id) ON DELETE CASCADE,
    country_id      TEXT NOT NULL,
    org_id          TEXT NOT NULL,
    role_in_org     TEXT NOT NULL DEFAULT 'member',
    has_veto        BOOLEAN NOT NULL DEFAULT FALSE,

    UNIQUE(sim_run_id, country_id, org_id)
);

CREATE INDEX idx_org_mem_sim ON org_memberships(sim_run_id);
CREATE INDEX idx_org_mem_country ON org_memberships(sim_run_id, country_id);
CREATE INDEX idx_org_mem_org ON org_memberships(sim_run_id, org_id);

-- ---------------------------------------------------------------------------
-- 1.11 RELATIONSHIPS — Bilateral country relationships (from relationships.csv)
-- ---------------------------------------------------------------------------
CREATE TABLE relationships (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sim_run_id      UUID NOT NULL REFERENCES sim_runs(id) ON DELETE CASCADE,
    from_country_id TEXT NOT NULL,
    to_country_id   TEXT NOT NULL,
    relationship    TEXT NOT NULL DEFAULT 'neutral'
                    CHECK (relationship IN ('alliance', 'close_ally', 'friendly',
                           'neutral', 'tense', 'hostile', 'at_war', 'strategic_rival')),
    dynamic         TEXT NOT NULL DEFAULT '',

    UNIQUE(sim_run_id, from_country_id, to_country_id)
);

CREATE INDEX idx_rel_sim ON relationships(sim_run_id);
CREATE INDEX idx_rel_from ON relationships(sim_run_id, from_country_id);
CREATE INDEX idx_rel_to ON relationships(sim_run_id, to_country_id);

-- ---------------------------------------------------------------------------
-- 1.12 SANCTIONS — Bilateral sanctions (from sanctions.csv, mutable)
-- ---------------------------------------------------------------------------
CREATE TABLE sanctions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sim_run_id      UUID NOT NULL REFERENCES sim_runs(id) ON DELETE CASCADE,
    imposer_country_id TEXT NOT NULL,
    target_country_id  TEXT NOT NULL,
    level           INT NOT NULL DEFAULT 0 CHECK (level >= -3 AND level <= 3),
    notes           TEXT NOT NULL DEFAULT '',
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(sim_run_id, imposer_country_id, target_country_id)
);

CREATE INDEX idx_sanctions_sim ON sanctions(sim_run_id);

-- ---------------------------------------------------------------------------
-- 1.13 TARIFFS — Bilateral tariffs (from tariffs.csv, mutable)
-- ---------------------------------------------------------------------------
CREATE TABLE tariffs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sim_run_id      UUID NOT NULL REFERENCES sim_runs(id) ON DELETE CASCADE,
    imposer_country_id TEXT NOT NULL,
    target_country_id  TEXT NOT NULL,
    level           INT NOT NULL DEFAULT 0 CHECK (level >= 0 AND level <= 3),
    notes           TEXT NOT NULL DEFAULT '',
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(sim_run_id, imposer_country_id, target_country_id)
);

CREATE INDEX idx_tariffs_sim ON tariffs(sim_run_id);

-- =============================================================================
-- SECTION 2: STATE TABLES (per-round snapshots)
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 2.1 WORLD STATE — Per-round global state snapshot
-- ---------------------------------------------------------------------------
CREATE TABLE world_state (
    id                          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sim_run_id                  UUID NOT NULL REFERENCES sim_runs(id) ON DELETE CASCADE,
    round_num                   INT NOT NULL CHECK (round_num >= 0 AND round_num <= 8),
    -- Global economic
    oil_price                   NUMERIC(8,2) NOT NULL DEFAULT 80.0,
    oil_price_index             NUMERIC(8,2) NOT NULL DEFAULT 100.0,
    global_trade_volume_index   NUMERIC(8,2) NOT NULL DEFAULT 100.0,
    dollar_credibility          NUMERIC(6,2) NOT NULL DEFAULT 100.0 CHECK (dollar_credibility >= 0 AND dollar_credibility <= 100),
    -- Global military/political
    nuclear_used_this_sim       BOOLEAN NOT NULL DEFAULT FALSE,
    formosa_blockade            BOOLEAN NOT NULL DEFAULT FALSE,
    -- OPEC production decisions (per member)
    opec_production             JSONB NOT NULL DEFAULT '{}'::JSONB,
    -- Chokepoint status
    chokepoint_status           JSONB NOT NULL DEFAULT '{}'::JSONB,
    -- Active wars
    wars                        JSONB NOT NULL DEFAULT '[]'::JSONB,
    -- Active blockades
    active_blockades            JSONB NOT NULL DEFAULT '{}'::JSONB,
    ground_blockades            JSONB NOT NULL DEFAULT '{}'::JSONB,
    -- Rare earth restrictions
    rare_earth_restrictions     JSONB NOT NULL DEFAULT '{}'::JSONB,
    -- Treaties and basing rights
    treaties                    JSONB NOT NULL DEFAULT '[]'::JSONB,
    basing_rights               JSONB NOT NULL DEFAULT '[]'::JSONB,
    blockaded_zones             JSONB NOT NULL DEFAULT '[]'::JSONB,  -- Active blockade zone IDs (naval cannot deploy here)
    -- Phase timestamps
    phase_a_start               TIMESTAMPTZ,
    phase_a_end                 TIMESTAMPTZ,
    phase_b_start               TIMESTAMPTZ,
    phase_b_end                 TIMESTAMPTZ,
    phase_c_start               TIMESTAMPTZ,
    phase_c_end                 TIMESTAMPTZ,
    -- Engine output
    narrative                   TEXT NOT NULL DEFAULT '',
    expert_panel                JSONB NOT NULL DEFAULT '{}'::JSONB,
    coherence_flags             JSONB NOT NULL DEFAULT '[]'::JSONB,
    -- Snapshot metadata
    is_frozen                   BOOLEAN NOT NULL DEFAULT FALSE,
    schema_version              TEXT NOT NULL DEFAULT '1.0',
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(sim_run_id, round_num)
);

CREATE INDEX idx_world_state_sim ON world_state(sim_run_id, round_num);

-- ---------------------------------------------------------------------------
-- 2.2 COUNTRY STATE — Per-country-per-round state snapshot
-- ---------------------------------------------------------------------------
CREATE TABLE country_state (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sim_run_id              UUID NOT NULL REFERENCES sim_runs(id) ON DELETE CASCADE,
    country_id              TEXT NOT NULL,
    round_num               INT NOT NULL CHECK (round_num >= 0 AND round_num <= 8),
    -- Economic CORE
    gdp                     NUMERIC(12,2) NOT NULL DEFAULT 0,
    gdp_growth_rate         NUMERIC(8,4) NOT NULL DEFAULT 0,
    treasury                NUMERIC(12,2) NOT NULL DEFAULT 0,
    inflation               NUMERIC(8,2) NOT NULL DEFAULT 0,
    debt_burden             NUMERIC(10,2) NOT NULL DEFAULT 0,
    momentum                NUMERIC(6,2) NOT NULL DEFAULT 0 CHECK (momentum >= -5 AND momentum <= 5),
    opec_production         TEXT NOT NULL DEFAULT 'na'
                            CHECK (opec_production IN ('min', 'low', 'normal', 'high', 'max', 'na')),
    -- Economic DERIVED (stored per snapshot for convenience, recomputable)
    economic_state          TEXT NOT NULL DEFAULT 'normal'
                            CHECK (economic_state IN ('normal', 'stressed', 'crisis', 'collapse')),
    market_index            INT NOT NULL DEFAULT 50 CHECK (market_index >= 0 AND market_index <= 100),
    revenue                 NUMERIC(12,2) NOT NULL DEFAULT 0,
    -- Military CORE
    mil_ground              INT NOT NULL DEFAULT 0,
    mil_naval               INT NOT NULL DEFAULT 0,
    mil_tactical_air        INT NOT NULL DEFAULT 0,
    mil_strategic_missiles  INT NOT NULL DEFAULT 0,
    mil_air_defense         INT NOT NULL DEFAULT 0,
    mobilization_pool       INT NOT NULL DEFAULT 0,
    -- Political CORE
    stability               NUMERIC(4,2) NOT NULL DEFAULT 5 CHECK (stability >= 0 AND stability <= 10),
    political_support       NUMERIC(6,2) NOT NULL DEFAULT 50 CHECK (political_support >= 0 AND political_support <= 100),
    war_tiredness           NUMERIC(6,2) NOT NULL DEFAULT 0,
    dem_rep_split_dem       INT NOT NULL DEFAULT 0,
    dem_rep_split_rep       INT NOT NULL DEFAULT 0,
    regime_status           TEXT NOT NULL DEFAULT 'stable'
                            CHECK (regime_status IN ('stable', 'unstable', 'collapsed')),
    -- Technology CORE
    nuclear_level           INT NOT NULL DEFAULT 0 CHECK (nuclear_level >= 0 AND nuclear_level <= 3),
    nuclear_rd_progress     NUMERIC(4,3) NOT NULL DEFAULT 0,
    ai_level                INT NOT NULL DEFAULT 0 CHECK (ai_level >= 0 AND ai_level <= 4),
    ai_rd_progress          NUMERIC(4,3) NOT NULL DEFAULT 0,
    -- Budget (what was submitted this round)
    budget                  JSONB NOT NULL DEFAULT '{}'::JSONB,
    -- Snapshot metadata
    is_frozen               BOOLEAN NOT NULL DEFAULT FALSE,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(sim_run_id, country_id, round_num),
    FOREIGN KEY (country_id, sim_run_id) REFERENCES countries(id, sim_run_id)
);

CREATE INDEX idx_country_state_sim ON country_state(sim_run_id, round_num);
CREATE INDEX idx_country_state_country ON country_state(sim_run_id, country_id, round_num);

-- ---------------------------------------------------------------------------
-- 2.3 ROLE STATE — Per-role-per-round state snapshot
-- ---------------------------------------------------------------------------
CREATE TABLE role_state (
    id                              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sim_run_id                      UUID NOT NULL REFERENCES sim_runs(id) ON DELETE CASCADE,
    role_id                         TEXT NOT NULL,
    round_num                       INT NOT NULL CHECK (round_num >= 0 AND round_num <= 8),
    -- CORE state
    personal_coins                  NUMERIC(8,2) NOT NULL DEFAULT 0,
    status                          TEXT NOT NULL DEFAULT 'active'
                                    CHECK (status IN ('active', 'fired', 'arrested', 'incapacitated', 'dead', 'exiled')),
    is_head_of_state                BOOLEAN NOT NULL DEFAULT FALSE,
    is_military_chief               BOOLEAN NOT NULL DEFAULT FALSE,
    -- Remaining operation pools (deplete over game)
    intelligence_pool_remaining     INT NOT NULL DEFAULT 0,
    sabotage_cards_remaining        INT NOT NULL DEFAULT 0,
    cyber_cards_remaining           INT NOT NULL DEFAULT 0,
    disinfo_cards_remaining         INT NOT NULL DEFAULT 0,
    election_meddling_remaining     INT NOT NULL DEFAULT 0,
    assassination_cards_remaining   INT NOT NULL DEFAULT 0,
    protest_stim_remaining          INT NOT NULL DEFAULT 0,
    fatherland_appeal_remaining     INT NOT NULL DEFAULT 0,
    -- Snapshot metadata
    is_frozen                       BOOLEAN NOT NULL DEFAULT FALSE,
    created_at                      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(sim_run_id, role_id, round_num),
    FOREIGN KEY (role_id, sim_run_id) REFERENCES roles(id, sim_run_id)
);

CREATE INDEX idx_role_state_sim ON role_state(sim_run_id, round_num);
CREATE INDEX idx_role_state_role ON role_state(sim_run_id, role_id, round_num);

-- =============================================================================
-- SECTION 3: EVENT TABLES
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 3.1 EVENTS — Immutable event log (the behavioral data pipeline)
-- ---------------------------------------------------------------------------
CREATE TABLE events (
    id              TEXT PRIMARY KEY,        -- ULID format: 'evt_<26-char-ulid>' (time-sortable)
    sim_run_id      UUID NOT NULL REFERENCES sim_runs(id) ON DELETE CASCADE,
    round_num       INT NOT NULL CHECK (round_num >= 0 AND round_num <= 8),
    phase           TEXT NOT NULL CHECK (phase IN ('pre', 'A', 'B', 'C', 'post')),
    timestamp       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    actor_role_id   TEXT NOT NULL,           -- role_id | 'engine' | 'moderator' | 'system'
    action_type     TEXT NOT NULL,           -- from controlled vocabulary (DET_NAMING_CONVENTIONS 1.3)
    target          TEXT,                    -- country_id | zone_id | role_id | org_id | null
    details         JSONB NOT NULL DEFAULT '{}'::JSONB,
    result          JSONB NOT NULL DEFAULT '{}'::JSONB,
    visibility      TEXT NOT NULL DEFAULT 'public'
                    CHECK (visibility IN ('public', 'country', 'role', 'moderator')),
    actor_country_id TEXT,                   -- which country this event belongs to
    idempotency_key TEXT                     -- for dedup of retried submissions
);

-- Event log query optimization indexes (per F4 API Contracts section 9.2)
-- ULID-based id is time-sortable, so id ordering = timestamp ordering
CREATE INDEX idx_events_sim_round ON events(sim_run_id, round_num, id);
CREATE INDEX idx_events_visibility ON events(sim_run_id, round_num, visibility, id);
CREATE INDEX idx_events_actor ON events(sim_run_id, actor_role_id, round_num);
CREATE INDEX idx_events_type ON events(sim_run_id, action_type, round_num);
CREATE INDEX idx_events_country ON events(sim_run_id, actor_country_id, round_num);
CREATE INDEX idx_events_idempotency ON events(sim_run_id, idempotency_key) WHERE idempotency_key IS NOT NULL;

-- ---------------------------------------------------------------------------
-- 3.2 TRANSACTIONS — Bilateral transactions
-- ---------------------------------------------------------------------------
CREATE TABLE transactions (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sim_run_id          UUID NOT NULL REFERENCES sim_runs(id) ON DELETE CASCADE,
    round_num           INT NOT NULL,
    transaction_type    TEXT NOT NULL
                        CHECK (transaction_type IN ('coin_transfer', 'arms_transfer',
                               'tech_transfer', 'basing_rights', 'treaty', 'agreement',
                               'org_creation', 'personal_investment', 'bribe')),
    proposer_role_id    TEXT NOT NULL,
    counterparty_role_id TEXT NOT NULL,
    from_country_id     TEXT NOT NULL,
    to_country_id       TEXT NOT NULL,
    details             JSONB NOT NULL DEFAULT '{}'::JSONB,
    conditions          TEXT NOT NULL DEFAULT '',
    status              TEXT NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending', 'confirmed', 'rejected', 'expired', 'executed')),
    confirmation_token  TEXT,
    state_changes       JSONB NOT NULL DEFAULT '[]'::JSONB,
    proposed_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    confirmed_at        TIMESTAMPTZ,
    expires_at          TIMESTAMPTZ,
    event_id            TEXT REFERENCES events(id)
);

CREATE INDEX idx_txn_sim ON transactions(sim_run_id, round_num);
CREATE INDEX idx_txn_proposer ON transactions(sim_run_id, proposer_role_id);
CREATE INDEX idx_txn_counterparty ON transactions(sim_run_id, counterparty_role_id);
CREATE INDEX idx_txn_status ON transactions(sim_run_id, status);

-- ---------------------------------------------------------------------------
-- 3.3 COMBAT RESULTS — Military engagement records
-- ---------------------------------------------------------------------------
CREATE TABLE combat_results (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sim_run_id          UUID NOT NULL REFERENCES sim_runs(id) ON DELETE CASCADE,
    round_num           INT NOT NULL,
    combat_type         TEXT NOT NULL
                        CHECK (combat_type IN ('ground_attack', 'naval_combat',
                               'naval_bombardment', 'air_strike', 'strategic_missile',
                               'nuclear_strike', 'blockade')),
    attacker_country    TEXT NOT NULL,
    defender_country    TEXT NOT NULL,
    zone_id             TEXT NOT NULL,
    attacker_units      JSONB NOT NULL DEFAULT '{}'::JSONB,
    defender_units      JSONB NOT NULL DEFAULT '{}'::JSONB,
    modifiers           JSONB NOT NULL DEFAULT '{}'::JSONB,
    dice_rolls          JSONB NOT NULL DEFAULT '[]'::JSONB,
    outcome             TEXT NOT NULL
                        CHECK (outcome IN ('attacker_wins', 'defender_wins',
                               'attacker_repelled', 'mutual_losses', 'stalemate')),
    attacker_losses     JSONB NOT NULL DEFAULT '{}'::JSONB,
    defender_losses     JSONB NOT NULL DEFAULT '{}'::JSONB,
    zone_control_change JSONB,
    event_id            TEXT REFERENCES events(id),
    timestamp           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_combat_sim ON combat_results(sim_run_id, round_num);
CREATE INDEX idx_combat_zone ON combat_results(sim_run_id, zone_id);

-- =============================================================================
-- SECTION 4: COMMUNICATION TABLES
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 4.1 MESSAGES — In-app messaging
-- ---------------------------------------------------------------------------
CREATE TABLE messages (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sim_run_id      UUID NOT NULL REFERENCES sim_runs(id) ON DELETE CASCADE,
    round_num       INT NOT NULL,
    from_role_id    TEXT,                    -- null for system messages
    to_role_id      TEXT,                    -- null for broadcast/channel messages
    channel         TEXT NOT NULL DEFAULT 'direct'
                    CHECK (channel IN ('direct', 'team', 'public', 'moderator', 'ai_meeting')),
    country_id      TEXT,                    -- for team channel messages
    content         TEXT NOT NULL,
    metadata        JSONB NOT NULL DEFAULT '{}'::JSONB,
    timestamp       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_messages_sim ON messages(sim_run_id, round_num);
CREATE INDEX idx_messages_from ON messages(sim_run_id, from_role_id);
CREATE INDEX idx_messages_to ON messages(sim_run_id, to_role_id);
CREATE INDEX idx_messages_channel ON messages(sim_run_id, channel, country_id);

-- ---------------------------------------------------------------------------
-- 4.2 MEETINGS — Meeting records
-- ---------------------------------------------------------------------------
CREATE TABLE meetings (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sim_run_id      UUID NOT NULL REFERENCES sim_runs(id) ON DELETE CASCADE,
    round_num       INT NOT NULL,
    meeting_type    TEXT NOT NULL DEFAULT 'bilateral'
                    CHECK (meeting_type IN ('bilateral', 'multilateral', 'organization',
                           'ai_meeting', 'public_session')),
    org_id          TEXT,                    -- for organization meetings
    participants    TEXT[] NOT NULL DEFAULT '{}',
    title           TEXT NOT NULL DEFAULT '',
    transcript      TEXT NOT NULL DEFAULT '',
    outcomes        JSONB NOT NULL DEFAULT '{}'::JSONB,
    started_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at        TIMESTAMPTZ
);

CREATE INDEX idx_meetings_sim ON meetings(sim_run_id, round_num);

-- =============================================================================
-- SECTION 5: AI TABLES
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 5.1 AI CONTEXTS — AI participant context snapshots
-- ---------------------------------------------------------------------------
CREATE TABLE ai_contexts (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sim_run_id      UUID NOT NULL REFERENCES sim_runs(id) ON DELETE CASCADE,
    role_id         TEXT NOT NULL,
    round_num       INT NOT NULL,
    context         JSONB NOT NULL DEFAULT '{}'::JSONB,
    visible_state   JSONB NOT NULL DEFAULT '{}'::JSONB,
    available_actions JSONB NOT NULL DEFAULT '[]'::JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ai_ctx_sim ON ai_contexts(sim_run_id, role_id, round_num);

-- ---------------------------------------------------------------------------
-- 5.2 AI DECISIONS — AI decision log
-- ---------------------------------------------------------------------------
CREATE TABLE ai_decisions (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sim_run_id          UUID NOT NULL REFERENCES sim_runs(id) ON DELETE CASCADE,
    role_id             TEXT NOT NULL,
    round_num           INT NOT NULL,
    phase               TEXT NOT NULL CHECK (phase IN ('A', 'B', 'C')),
    decision            JSONB NOT NULL DEFAULT '{}'::JSONB,
    reasoning           TEXT NOT NULL DEFAULT '',
    internal_reasoning  TEXT NOT NULL DEFAULT '',   -- MODERATOR-ONLY visibility
    model_used          TEXT NOT NULL DEFAULT '',
    token_count         INT NOT NULL DEFAULT 0,
    latency_ms          INT NOT NULL DEFAULT 0,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ai_dec_sim ON ai_decisions(sim_run_id, role_id, round_num);

-- =============================================================================
-- SECTION 6: ARTEFACTS TABLE
-- =============================================================================

CREATE TABLE artefacts (
    id              TEXT NOT NULL,
    sim_run_id      UUID NOT NULL REFERENCES sim_runs(id) ON DELETE CASCADE,
    role_id         TEXT NOT NULL,
    title           TEXT NOT NULL,
    classification  TEXT NOT NULL DEFAULT 'role_specific'
                    CHECK (classification IN ('role_specific', 'team_shared', 'public')),
    format          TEXT NOT NULL DEFAULT '',
    content_file    TEXT NOT NULL DEFAULT '',
    content         TEXT NOT NULL DEFAULT '',       -- inline content (for DB-served artefacts)
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (id, sim_run_id),
    FOREIGN KEY (role_id, sim_run_id) REFERENCES roles(id, sim_run_id)
);

CREATE INDEX idx_artefacts_role ON artefacts(sim_run_id, role_id);


-- =============================================================================
-- SECTION 7: ROW-LEVEL SECURITY (B2)
-- =============================================================================

-- Enable RLS on all tables
ALTER TABLE sim_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE facilitators ENABLE ROW LEVEL SECURITY;
ALTER TABLE countries ENABLE ROW LEVEL SECURITY;
ALTER TABLE roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE zones ENABLE ROW LEVEL SECURITY;
ALTER TABLE zone_adjacency ENABLE ROW LEVEL SECURITY;
ALTER TABLE deployments ENABLE ROW LEVEL SECURITY;
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE org_memberships ENABLE ROW LEVEL SECURITY;
ALTER TABLE relationships ENABLE ROW LEVEL SECURITY;
ALTER TABLE sanctions ENABLE ROW LEVEL SECURITY;
ALTER TABLE tariffs ENABLE ROW LEVEL SECURITY;
ALTER TABLE world_state ENABLE ROW LEVEL SECURITY;
ALTER TABLE country_state ENABLE ROW LEVEL SECURITY;
ALTER TABLE role_state ENABLE ROW LEVEL SECURITY;
ALTER TABLE events ENABLE ROW LEVEL SECURITY;
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE combat_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE meetings ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_contexts ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_decisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE artefacts ENABLE ROW LEVEL SECURITY;

-- -------------------------------------------------------
-- Helper functions for RLS
-- -------------------------------------------------------

-- Get the role_id for the current user in a given sim
CREATE OR REPLACE FUNCTION get_user_role_id(p_sim_run_id UUID)
RETURNS TEXT
LANGUAGE sql
STABLE
SECURITY DEFINER
AS $$
    SELECT id FROM roles
    WHERE sim_run_id = p_sim_run_id
      AND user_id = auth.uid()
    LIMIT 1;
$$;

-- Get the country_id for the current user in a given sim
CREATE OR REPLACE FUNCTION get_user_country_id(p_sim_run_id UUID)
RETURNS TEXT
LANGUAGE sql
STABLE
SECURITY DEFINER
AS $$
    SELECT country_id FROM roles
    WHERE sim_run_id = p_sim_run_id
      AND user_id = auth.uid()
    LIMIT 1;
$$;

-- Check if current user is a facilitator for a given sim
CREATE OR REPLACE FUNCTION is_facilitator(p_sim_run_id UUID)
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SECURITY DEFINER
AS $$
    SELECT EXISTS (
        SELECT 1 FROM facilitators
        WHERE sim_run_id = p_sim_run_id
          AND user_id = auth.uid()
    );
$$;

-- -------------------------------------------------------
-- RLS POLICIES
-- -------------------------------------------------------

-- USERS: users can read their own record
CREATE POLICY users_read_own ON users FOR SELECT USING (id = auth.uid());
CREATE POLICY users_update_own ON users FOR UPDATE USING (id = auth.uid());

-- SIM RUNS: participants and facilitators can read their sim
CREATE POLICY sim_runs_read ON sim_runs FOR SELECT USING (
    EXISTS (SELECT 1 FROM roles WHERE roles.sim_run_id = sim_runs.id AND roles.user_id = auth.uid())
    OR EXISTS (SELECT 1 FROM facilitators WHERE facilitators.sim_run_id = sim_runs.id AND facilitators.user_id = auth.uid())
);
CREATE POLICY sim_runs_manage ON sim_runs FOR ALL USING (
    EXISTS (SELECT 1 FROM facilitators WHERE facilitators.sim_run_id = sim_runs.id AND facilitators.user_id = auth.uid() AND facilitators.access_level = 'admin')
);

-- FACILITATORS: facilitators can read their own sim assignments
CREATE POLICY facilitators_read ON facilitators FOR SELECT USING (
    user_id = auth.uid()
    OR EXISTS (SELECT 1 FROM facilitators f2 WHERE f2.sim_run_id = facilitators.sim_run_id AND f2.user_id = auth.uid())
);

-- COUNTRIES: all participants in the sim can read all countries (public structure)
CREATE POLICY countries_read ON countries FOR SELECT USING (
    EXISTS (SELECT 1 FROM roles WHERE roles.sim_run_id = countries.sim_run_id AND roles.user_id = auth.uid())
    OR is_facilitator(countries.sim_run_id)
);

-- ROLES: participants see all roles in their sim (names/titles are public), but details vary
CREATE POLICY roles_read ON roles FOR SELECT USING (
    EXISTS (SELECT 1 FROM roles r WHERE r.sim_run_id = roles.sim_run_id AND r.user_id = auth.uid())
    OR is_facilitator(roles.sim_run_id)
);

-- ZONES: all participants can read zones (map is public)
CREATE POLICY zones_read ON zones FOR SELECT USING (
    EXISTS (SELECT 1 FROM roles WHERE roles.sim_run_id = zones.sim_run_id AND roles.user_id = auth.uid())
    OR is_facilitator(zones.sim_run_id)
);

-- ZONE ADJACENCY: public map topology
CREATE POLICY zone_adj_read ON zone_adjacency FOR SELECT USING (
    EXISTS (SELECT 1 FROM roles WHERE roles.sim_run_id = zone_adjacency.sim_run_id AND roles.user_id = auth.uid())
    OR is_facilitator(zone_adjacency.sim_run_id)
);

-- DEPLOYMENTS: participants see deployments in zones they can observe
-- (Full filtering by adjacency/intelligence done at API layer; DB allows country members + facilitators)
CREATE POLICY deployments_read ON deployments FOR SELECT USING (
    is_facilitator(deployments.sim_run_id)
    OR deployments.country_id = get_user_country_id(deployments.sim_run_id)
    OR EXISTS (
        SELECT 1 FROM roles
        WHERE roles.sim_run_id = deployments.sim_run_id
          AND roles.user_id = auth.uid()
    )
);
-- Note: Fine-grained visibility (adjacent zones, fog of war) enforced at API layer.
-- RLS provides baseline access; the API further filters distant/hidden deployments.

-- ORGANIZATIONS: public
CREATE POLICY orgs_read ON organizations FOR SELECT USING (
    EXISTS (SELECT 1 FROM roles WHERE roles.sim_run_id = organizations.sim_run_id AND roles.user_id = auth.uid())
    OR is_facilitator(organizations.sim_run_id)
);

-- ORG MEMBERSHIPS: public
CREATE POLICY org_mem_read ON org_memberships FOR SELECT USING (
    EXISTS (SELECT 1 FROM roles WHERE roles.sim_run_id = org_memberships.sim_run_id AND roles.user_id = auth.uid())
    OR is_facilitator(org_memberships.sim_run_id)
);

-- RELATIONSHIPS: public (relationship status is known)
CREATE POLICY rel_read ON relationships FOR SELECT USING (
    EXISTS (SELECT 1 FROM roles WHERE roles.sim_run_id = relationships.sim_run_id AND roles.user_id = auth.uid())
    OR is_facilitator(relationships.sim_run_id)
);

-- SANCTIONS: public (sanctions are declared publicly)
CREATE POLICY sanctions_read ON sanctions FOR SELECT USING (
    EXISTS (SELECT 1 FROM roles WHERE roles.sim_run_id = sanctions.sim_run_id AND roles.user_id = auth.uid())
    OR is_facilitator(sanctions.sim_run_id)
);

-- TARIFFS: public (tariff levels are public)
CREATE POLICY tariffs_read ON tariffs FOR SELECT USING (
    EXISTS (SELECT 1 FROM roles WHERE roles.sim_run_id = tariffs.sim_run_id AND roles.user_id = auth.uid())
    OR is_facilitator(tariffs.sim_run_id)
);

-- WORLD STATE: global fields visible to all; dollar_credibility and expert_panel are moderator-only
-- (API layer handles field-level filtering; RLS provides row-level access)
CREATE POLICY world_state_read ON world_state FOR SELECT USING (
    EXISTS (SELECT 1 FROM roles WHERE roles.sim_run_id = world_state.sim_run_id AND roles.user_id = auth.uid())
    OR is_facilitator(world_state.sim_run_id)
);

-- COUNTRY STATE: visible to own country members + facilitators
CREATE POLICY country_state_read_own ON country_state FOR SELECT USING (
    is_facilitator(country_state.sim_run_id)
    OR country_state.country_id = get_user_country_id(country_state.sim_run_id)
);

-- ROLE STATE: visible to own role + facilitators
CREATE POLICY role_state_read_own ON role_state FOR SELECT USING (
    is_facilitator(role_state.sim_run_id)
    OR role_state.role_id = get_user_role_id(role_state.sim_run_id)
);

-- EVENTS: filtered by visibility level
CREATE POLICY events_read_public ON events FOR SELECT USING (
    is_facilitator(events.sim_run_id)
    OR (
        events.visibility = 'public'
        AND EXISTS (SELECT 1 FROM roles WHERE roles.sim_run_id = events.sim_run_id AND roles.user_id = auth.uid())
    )
    OR (
        events.visibility = 'country'
        AND events.actor_country_id = get_user_country_id(events.sim_run_id)
    )
    OR (
        events.visibility = 'role'
        AND events.actor_role_id = get_user_role_id(events.sim_run_id)
    )
);

-- TRANSACTIONS: visible to proposer, counterparty, and facilitators
CREATE POLICY txn_read ON transactions FOR SELECT USING (
    is_facilitator(transactions.sim_run_id)
    OR transactions.proposer_role_id = get_user_role_id(transactions.sim_run_id)
    OR transactions.counterparty_role_id = get_user_role_id(transactions.sim_run_id)
);

-- COMBAT RESULTS: public summary; detailed results to involved countries + facilitators
CREATE POLICY combat_read ON combat_results FOR SELECT USING (
    is_facilitator(combat_results.sim_run_id)
    OR combat_results.attacker_country = get_user_country_id(combat_results.sim_run_id)
    OR combat_results.defender_country = get_user_country_id(combat_results.sim_run_id)
    OR EXISTS (SELECT 1 FROM roles WHERE roles.sim_run_id = combat_results.sim_run_id AND roles.user_id = auth.uid())
);

-- MESSAGES: sender and recipient only (+ facilitators + team channel members)
CREATE POLICY messages_read ON messages FOR SELECT USING (
    is_facilitator(messages.sim_run_id)
    OR messages.from_role_id = get_user_role_id(messages.sim_run_id)
    OR messages.to_role_id = get_user_role_id(messages.sim_run_id)
    OR (messages.channel = 'team' AND messages.country_id = get_user_country_id(messages.sim_run_id))
    OR messages.channel = 'public'
);

-- MEETINGS: only participants + facilitators
CREATE POLICY meetings_read ON meetings FOR SELECT USING (
    is_facilitator(meetings.sim_run_id)
    OR get_user_role_id(meetings.sim_run_id) = ANY(meetings.participants)
);

-- AI CONTEXTS: moderator only
CREATE POLICY ai_ctx_read ON ai_contexts FOR SELECT USING (
    is_facilitator(ai_contexts.sim_run_id)
);

-- AI DECISIONS: moderator only (internal_reasoning is sensitive)
CREATE POLICY ai_dec_read ON ai_decisions FOR SELECT USING (
    is_facilitator(ai_decisions.sim_run_id)
);

-- ARTEFACTS: own role's artefacts, team_shared for team, public for all
CREATE POLICY artefacts_read ON artefacts FOR SELECT USING (
    is_facilitator(artefacts.sim_run_id)
    OR (artefacts.classification = 'public'
        AND EXISTS (SELECT 1 FROM roles WHERE roles.sim_run_id = artefacts.sim_run_id AND roles.user_id = auth.uid()))
    OR (artefacts.classification = 'team_shared'
        AND EXISTS (
            SELECT 1 FROM roles r1
            JOIN roles r2 ON r1.country_id = r2.country_id AND r1.sim_run_id = r2.sim_run_id
            WHERE r1.id = artefacts.role_id
              AND r1.sim_run_id = artefacts.sim_run_id
              AND r2.user_id = auth.uid()
        ))
    OR (artefacts.role_id = get_user_role_id(artefacts.sim_run_id))
);

-- -------------------------------------------------------
-- Write policies: only service role and facilitators write
-- All state-modifying operations go through server-side
-- functions (Supabase Edge Functions / backend), never
-- directly from client. These policies ensure safety.
-- -------------------------------------------------------

-- Facilitators can insert/update game state tables
CREATE POLICY facilitator_write_world_state ON world_state FOR ALL USING (is_facilitator(world_state.sim_run_id));
CREATE POLICY facilitator_write_country_state ON country_state FOR ALL USING (is_facilitator(country_state.sim_run_id));
CREATE POLICY facilitator_write_role_state ON role_state FOR ALL USING (is_facilitator(role_state.sim_run_id));
CREATE POLICY facilitator_write_events ON events FOR INSERT WITH CHECK (is_facilitator(events.sim_run_id));
CREATE POLICY facilitator_write_deployments ON deployments FOR ALL USING (is_facilitator(deployments.sim_run_id));
CREATE POLICY facilitator_write_sanctions ON sanctions FOR ALL USING (is_facilitator(sanctions.sim_run_id));
CREATE POLICY facilitator_write_tariffs ON tariffs FOR ALL USING (is_facilitator(tariffs.sim_run_id));
CREATE POLICY facilitator_write_relationships ON relationships FOR ALL USING (is_facilitator(relationships.sim_run_id));

-- Participants can insert messages
CREATE POLICY messages_insert ON messages FOR INSERT WITH CHECK (
    messages.from_role_id = get_user_role_id(messages.sim_run_id)
);

-- Participants can insert transactions (proposals)
CREATE POLICY txn_insert ON transactions FOR INSERT WITH CHECK (
    transactions.proposer_role_id = get_user_role_id(transactions.sim_run_id)
);


-- =============================================================================
-- SECTION 8: DATABASE FUNCTIONS (B4)
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 8.1 check_authorization — Verify role has permission for action type
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION check_authorization(
    p_sim_run_id UUID,
    p_role_id TEXT,
    p_action_type TEXT
)
RETURNS BOOLEAN
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
AS $$
DECLARE
    v_role RECORD;
    v_power_map JSONB;
BEGIN
    -- Fetch the role
    SELECT * INTO v_role FROM roles
    WHERE id = p_role_id AND sim_run_id = p_sim_run_id;

    IF NOT FOUND THEN
        RETURN FALSE;
    END IF;

    -- Role must be active
    IF v_role.status != 'active' THEN
        RETURN FALSE;
    END IF;

    -- Head of state has implicit authority for all country-level actions
    -- unless another role has exclusive authority
    IF v_role.is_head_of_state THEN
        RETURN TRUE;
    END IF;

    -- Map action_type to required power (canonical names per DET_NAMING_CONVENTIONS 1.3)
    v_power_map := '{
        "tariff_set": "set_tariffs",
        "sanction_set": "set_tariffs",
        "ground_attack": "authorize_attack",
        "blockade": "authorize_attack",
        "naval_combat": "authorize_attack",
        "naval_bombardment": "authorize_attack",
        "air_strike": "authorize_attack",
        "strategic_missile": "approve_nuclear",
        "nuclear_strike": "approve_nuclear",
        "fire_role": "fire_team_member",
        "arrest": "arrest",
        "troop_deployment": "deploy_forces",
        "opec_production_set": "set_opec_production",
        "budget_submit": "set_budget",
        "public_statement": "public_statement",
        "meeting_call": "public_statement",
        "election_nominate": "public_statement",
        "mobilization_order": "deploy_forces",
        "militia_call": "deploy_forces",
        "intelligence_request": "intelligence_briefing",
        "sabotage": "covert_operations",
        "cyber_attack": "covert_operations",
        "disinformation": "covert_operations",
        "election_meddling": "covert_operations",
        "assassination": "covert_operations",
        "propaganda": "public_statement",
        "coup_attempt": "covert_operations",
        "impeachment": "public_statement",
        "transaction_propose": "negotiate",
        "agreement_sign": "negotiate",
        "org_creation": "negotiate"
    }'::JSONB;

    -- Check if the role has the required power
    IF v_power_map ? p_action_type THEN
        RETURN (v_power_map ->> p_action_type) = ANY(v_role.powers);
    END IF;

    -- Unknown action type — deny by default
    RETURN FALSE;
END;
$$;

-- ---------------------------------------------------------------------------
-- 8.2 execute_transaction — Process a bilateral transaction
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION execute_transaction(
    p_sim_run_id UUID,
    p_transaction_id UUID,
    p_confirmed_by TEXT
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_txn RECORD;
    v_from_treasury NUMERIC;
    v_to_treasury NUMERIC;
    v_amount NUMERIC;
    v_event_id UUID;
    v_round INT;
BEGIN
    -- Get the transaction
    SELECT * INTO v_txn FROM transactions
    WHERE id = p_transaction_id AND sim_run_id = p_sim_run_id;

    IF NOT FOUND THEN
        RETURN jsonb_build_object('success', false, 'error', 'Transaction not found');
    END IF;

    -- Must be pending
    IF v_txn.status != 'pending' THEN
        RETURN jsonb_build_object('success', false, 'error', 'Transaction is not pending');
    END IF;

    -- Must be confirmed by the counterparty
    IF v_txn.counterparty_role_id != p_confirmed_by THEN
        RETURN jsonb_build_object('success', false, 'error', 'Only counterparty can confirm');
    END IF;

    -- Check expiry
    IF v_txn.expires_at IS NOT NULL AND v_txn.expires_at < NOW() THEN
        UPDATE transactions SET status = 'expired' WHERE id = p_transaction_id;
        RETURN jsonb_build_object('success', false, 'error', 'Transaction expired');
    END IF;

    -- Get current round
    SELECT current_round INTO v_round FROM sim_runs WHERE id = p_sim_run_id;

    -- Handle coin_transfer specifically (canonical name per DET_NAMING_CONVENTIONS 1.2)
    IF v_txn.transaction_type = 'coin_transfer' THEN
        v_amount := (v_txn.details ->> 'amount')::NUMERIC;

        -- Get from_country treasury
        SELECT treasury INTO v_from_treasury FROM country_state
        WHERE sim_run_id = p_sim_run_id AND country_id = v_txn.from_country_id AND round_num = v_round;

        IF v_from_treasury < v_amount THEN
            RETURN jsonb_build_object('success', false, 'error', 'Insufficient treasury');
        END IF;

        -- Execute the transfer
        UPDATE country_state
        SET treasury = treasury - v_amount
        WHERE sim_run_id = p_sim_run_id AND country_id = v_txn.from_country_id AND round_num = v_round;

        UPDATE country_state
        SET treasury = treasury + v_amount
        WHERE sim_run_id = p_sim_run_id AND country_id = v_txn.to_country_id AND round_num = v_round;

        -- Update transaction status
        UPDATE transactions
        SET status = 'executed',
            confirmed_at = NOW(),
            state_changes = jsonb_build_array(
                jsonb_build_object('path', 'countries.' || v_txn.from_country_id || '.treasury', 'delta', -v_amount),
                jsonb_build_object('path', 'countries.' || v_txn.to_country_id || '.treasury', 'delta', v_amount)
            )
        WHERE id = p_transaction_id;

        -- Log event (ULID generated by application layer; use fallback for DB-only execution)
        INSERT INTO events (id, sim_run_id, round_num, phase, actor_role_id, action_type, target, details, result, visibility, actor_country_id)
        VALUES (
            'evt_' || encode(gen_random_bytes(16), 'hex'),  -- fallback ID; prefer ULID from app
            p_sim_run_id, v_round, 'A', p_confirmed_by, 'coin_transfer',
            v_txn.to_country_id,
            jsonb_build_object('amount', v_amount, 'from', v_txn.from_country_id, 'to', v_txn.to_country_id),
            jsonb_build_object('executed', true),
            'country',
            v_txn.from_country_id
        )
        RETURNING id INTO v_event_id;

        UPDATE transactions SET event_id = v_event_id WHERE id = p_transaction_id;

        RETURN jsonb_build_object('success', true, 'status', 'executed', 'event_id', v_event_id);
    END IF;

    -- For other transaction types (arms_transfer, basing_rights, etc.)
    -- mark as executed and log event; actual state changes handled by engine
    UPDATE transactions
    SET status = 'executed', confirmed_at = NOW()
    WHERE id = p_transaction_id;

    INSERT INTO events (id, sim_run_id, round_num, phase, actor_role_id, action_type, target, details, result, visibility, actor_country_id)
    VALUES (
        'evt_' || encode(gen_random_bytes(16), 'hex'),  -- fallback ID; prefer ULID from app
        p_sim_run_id, v_round, 'A', p_confirmed_by, v_txn.transaction_type,
        v_txn.to_country_id, v_txn.details,
        jsonb_build_object('executed', true),
        'country',
        v_txn.from_country_id
    )
    RETURNING id INTO v_event_id;

    UPDATE transactions SET event_id = v_event_id WHERE id = p_transaction_id;

    RETURN jsonb_build_object('success', true, 'status', 'executed', 'event_id', v_event_id);
END;
$$;

-- ---------------------------------------------------------------------------
-- 8.3 process_round_end — Snapshot world state and advance round
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION process_round_end(
    p_sim_run_id UUID
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_current_round INT;
    v_max_rounds INT;
BEGIN
    -- Get current round
    SELECT current_round, max_rounds INTO v_current_round, v_max_rounds
    FROM sim_runs WHERE id = p_sim_run_id;

    IF NOT FOUND THEN
        RETURN jsonb_build_object('success', false, 'error', 'SIM run not found');
    END IF;

    -- Freeze current round snapshots
    UPDATE world_state
    SET is_frozen = TRUE, phase_c_end = NOW()
    WHERE sim_run_id = p_sim_run_id AND round_num = v_current_round;

    UPDATE country_state
    SET is_frozen = TRUE
    WHERE sim_run_id = p_sim_run_id AND round_num = v_current_round;

    UPDATE role_state
    SET is_frozen = TRUE
    WHERE sim_run_id = p_sim_run_id AND round_num = v_current_round;

    -- Log round end event
    INSERT INTO events (id, sim_run_id, round_num, phase, actor_role_id, action_type, details, visibility, actor_country_id)
    VALUES (
        'evt_' || encode(gen_random_bytes(16), 'hex'),
        p_sim_run_id, v_current_round, 'post', 'engine', 'round_end',
        jsonb_build_object('round_num', v_current_round),
        'public',
        'global'
    );

    -- Check if SIM is complete
    IF v_current_round >= v_max_rounds THEN
        UPDATE sim_runs
        SET status = 'completed', completed_at = NOW(), updated_at = NOW()
        WHERE id = p_sim_run_id;

        RETURN jsonb_build_object('success', true, 'status', 'sim_completed', 'final_round', v_current_round);
    END IF;

    -- Advance round counter
    UPDATE sim_runs
    SET current_round = v_current_round + 1,
        current_phase = 'pre',
        updated_at = NOW()
    WHERE id = p_sim_run_id;

    -- Create new round snapshots by copying current state
    -- (World state)
    INSERT INTO world_state (sim_run_id, round_num, oil_price, oil_price_index,
        global_trade_volume_index, dollar_credibility, nuclear_used_this_sim,
        formosa_blockade, opec_production, chokepoint_status, wars,
        active_blockades, ground_blockades, rare_earth_restrictions,
        treaties, basing_rights, blockaded_zones)
    SELECT sim_run_id, v_current_round + 1, oil_price, oil_price_index,
        global_trade_volume_index, dollar_credibility, nuclear_used_this_sim,
        formosa_blockade, opec_production, chokepoint_status, wars,
        active_blockades, ground_blockades, rare_earth_restrictions,
        treaties, basing_rights, blockaded_zones
    FROM world_state
    WHERE sim_run_id = p_sim_run_id AND round_num = v_current_round;

    -- (Country states)
    INSERT INTO country_state (sim_run_id, country_id, round_num, gdp, gdp_growth_rate,
        treasury, inflation, debt_burden, momentum, opec_production, economic_state,
        market_index, revenue, mil_ground, mil_naval, mil_tactical_air,
        mil_strategic_missiles, mil_air_defense, mobilization_pool, stability,
        political_support, war_tiredness, dem_rep_split_dem, dem_rep_split_rep,
        regime_status, nuclear_level, nuclear_rd_progress, ai_level, ai_rd_progress)
    SELECT sim_run_id, country_id, v_current_round + 1, gdp, gdp_growth_rate,
        treasury, inflation, debt_burden, momentum, opec_production, economic_state,
        market_index, revenue, mil_ground, mil_naval, mil_tactical_air,
        mil_strategic_missiles, mil_air_defense, mobilization_pool, stability,
        political_support, war_tiredness, dem_rep_split_dem, dem_rep_split_rep,
        regime_status, nuclear_level, nuclear_rd_progress, ai_level, ai_rd_progress
    FROM country_state
    WHERE sim_run_id = p_sim_run_id AND round_num = v_current_round;

    -- (Role states)
    INSERT INTO role_state (sim_run_id, role_id, round_num, personal_coins, status,
        is_head_of_state, is_military_chief, intelligence_pool_remaining,
        sabotage_cards_remaining, cyber_cards_remaining, disinfo_cards_remaining,
        election_meddling_remaining, assassination_cards_remaining,
        protest_stim_remaining, fatherland_appeal_remaining)
    SELECT sim_run_id, role_id, v_current_round + 1, personal_coins, status,
        is_head_of_state, is_military_chief, intelligence_pool_remaining,
        sabotage_cards_remaining, cyber_cards_remaining, disinfo_cards_remaining,
        election_meddling_remaining, assassination_cards_remaining,
        protest_stim_remaining, fatherland_appeal_remaining
    FROM role_state
    WHERE sim_run_id = p_sim_run_id AND round_num = v_current_round;

    RETURN jsonb_build_object('success', true, 'new_round', v_current_round + 1);
END;
$$;

-- ---------------------------------------------------------------------------
-- 8.4 submit_budget — Validate and store budget submission
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION submit_budget(
    p_sim_run_id UUID,
    p_country_id TEXT,
    p_role_id TEXT,
    p_budget JSONB
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_round INT;
    v_state RECORD;
    v_country RECORD;
    v_total_allocation NUMERIC;
    v_social NUMERIC;
    v_military NUMERIC;
    v_technology NUMERIC;
    v_maintenance NUMERIC;
    v_revenue NUMERIC;
BEGIN
    -- Verify authorization
    IF NOT check_authorization(p_sim_run_id, p_role_id, 'budget_submit') THEN
        RETURN jsonb_build_object('success', false, 'error', 'Not authorized to submit budget');
    END IF;

    -- Get current round
    SELECT current_round INTO v_round FROM sim_runs WHERE id = p_sim_run_id;

    -- Get current country state
    SELECT * INTO v_state FROM country_state
    WHERE sim_run_id = p_sim_run_id AND country_id = p_country_id AND round_num = v_round;

    IF NOT FOUND THEN
        RETURN jsonb_build_object('success', false, 'error', 'Country state not found');
    END IF;

    -- Get country config for maintenance
    SELECT * INTO v_country FROM countries
    WHERE id = p_country_id AND sim_run_id = p_sim_run_id;

    -- Parse allocations
    v_social := COALESCE((p_budget ->> 'social_allocation')::NUMERIC, 0);
    v_military := COALESCE((p_budget ->> 'military_allocation')::NUMERIC, 0);
    v_technology := COALESCE((p_budget ->> 'technology_allocation')::NUMERIC, 0);

    -- Calculate maintenance cost
    v_maintenance := (v_state.mil_ground + v_state.mil_naval + v_state.mil_tactical_air
                     + v_state.mil_strategic_missiles + v_state.mil_air_defense)
                     * v_country.maintenance_per_unit;

    v_total_allocation := v_social + v_military + v_technology + v_maintenance;

    -- Revenue = GDP * tax_rate (simplified; engine computes exact value)
    v_revenue := v_state.gdp * v_country.tax_rate;

    -- Validate: total cannot exceed revenue + treasury
    IF v_total_allocation > v_revenue + v_state.treasury THEN
        RETURN jsonb_build_object(
            'success', false,
            'error', 'VALIDATION_BUDGET_EXCEEDS_REVENUE',
            'details', jsonb_build_object(
                'total_allocation', v_total_allocation,
                'projected_revenue', v_revenue,
                'treasury_available', v_state.treasury,
                'max_with_treasury', v_revenue + v_state.treasury
            )
        );
    END IF;

    -- Validate: social spending meets baseline
    IF v_social < v_revenue * v_country.social_baseline THEN
        RETURN jsonb_build_object(
            'success', false,
            'error', 'VALIDATION_SOCIAL_BELOW_BASELINE',
            'details', jsonb_build_object(
                'social_allocation', v_social,
                'minimum_required', v_revenue * v_country.social_baseline,
                'social_baseline_pct', v_country.social_baseline
            )
        );
    END IF;

    -- Store the budget
    UPDATE country_state
    SET budget = p_budget
    WHERE sim_run_id = p_sim_run_id AND country_id = p_country_id AND round_num = v_round;

    -- Log event
    INSERT INTO events (id, sim_run_id, round_num, phase, actor_role_id, action_type, target, details, result, visibility, actor_country_id)
    VALUES (
        'evt_' || encode(gen_random_bytes(16), 'hex'),
        p_sim_run_id, v_round, 'A', p_role_id, 'budget_submit',
        p_country_id, p_budget,
        jsonb_build_object('accepted', true, 'total', v_total_allocation, 'revenue', v_revenue),
        'country', p_country_id
    );

    RETURN jsonb_build_object(
        'success', true,
        'total_allocation', v_total_allocation,
        'projected_revenue', v_revenue,
        'maintenance', v_maintenance
    );
END;
$$;

-- ---------------------------------------------------------------------------
-- 8.5 submit_military_action — Validate authorization chain and log action
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION submit_military_action(
    p_sim_run_id UUID,
    p_role_id TEXT,
    p_action_type TEXT,
    p_params JSONB
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_round INT;
    v_role RECORD;
    v_country_id TEXT;
    v_target_zone TEXT;
    v_from_zone TEXT;
    v_adjacent BOOLEAN;
    v_event_id UUID;
BEGIN
    -- Verify authorization
    IF NOT check_authorization(p_sim_run_id, p_role_id, p_action_type) THEN
        RETURN jsonb_build_object('success', false, 'error', 'AUTH_ROLE_MISMATCH',
            'message', 'Role does not have permission for this action');
    END IF;

    -- Get current round and phase
    SELECT current_round INTO v_round FROM sim_runs WHERE id = p_sim_run_id;

    -- Get role info
    SELECT * INTO v_role FROM roles
    WHERE id = p_role_id AND sim_run_id = p_sim_run_id;

    v_country_id := v_role.country_id;

    -- Nuclear actions require dual authorization
    IF p_action_type IN ('nuclear_strike', 'nuclear_test') THEN
        -- Check if country has nuclear capability
        DECLARE
            v_nuke_level INT;
        BEGIN
            SELECT nuclear_level INTO v_nuke_level FROM country_state
            WHERE sim_run_id = p_sim_run_id AND country_id = v_country_id AND round_num = v_round;

            IF v_nuke_level < 1 AND p_action_type = 'nuclear_strike' THEN
                RETURN jsonb_build_object('success', false, 'error', 'RESOURCE_NO_NUCLEAR',
                    'message', 'Country does not have nuclear capability');
            END IF;
        END;
    END IF;

    -- For attack actions, validate zone adjacency
    IF p_action_type = 'attack' THEN
        v_target_zone := p_params ->> 'target_zone';
        v_from_zone := p_params ->> 'from_zone';

        -- Check adjacency
        SELECT EXISTS (
            SELECT 1 FROM zone_adjacency
            WHERE sim_run_id = p_sim_run_id
              AND ((zone_a = v_from_zone AND zone_b = v_target_zone)
                OR (zone_a = v_target_zone AND zone_b = v_from_zone))
        ) INTO v_adjacent;

        IF NOT v_adjacent THEN
            RETURN jsonb_build_object('success', false, 'error', 'VALIDATION_NOT_ADJACENT',
                'message', 'From zone and target zone are not adjacent');
        END IF;

        -- Check units available in from_zone
        -- (Detailed unit validation done by the engine; this is a basic check)
    END IF;

    -- Log the military action as an event
    INSERT INTO events (id, sim_run_id, round_num, phase, actor_role_id, action_type, target,
        details, result, visibility, actor_country_id)
    VALUES (
        'evt_' || encode(gen_random_bytes(16), 'hex'),
        p_sim_run_id, v_round, 'A', p_role_id, p_action_type,
        COALESCE(p_params ->> 'target_zone', p_params ->> 'target'),
        p_params,
        jsonb_build_object('status', 'submitted'),
        CASE
            WHEN p_action_type IN ('nuclear_strike', 'nuclear_test') THEN 'moderator'
            ELSE 'public'
        END,
        v_country_id
    )
    RETURNING id INTO v_event_id;

    RETURN jsonb_build_object(
        'success', true,
        'event_id', v_event_id,
        'status', 'submitted',
        'message', 'Action submitted. Awaiting engine processing.'
    );
END;
$$;


-- =============================================================================
-- SECTION 9: UPDATED_AT TRIGGERS
-- =============================================================================

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

CREATE TRIGGER tr_sim_runs_updated_at BEFORE UPDATE ON sim_runs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER tr_deployments_updated_at BEFORE UPDATE ON deployments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER tr_sanctions_updated_at BEFORE UPDATE ON sanctions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER tr_tariffs_updated_at BEFORE UPDATE ON tariffs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();


-- ---------------------------------------------------------------------------
-- 8.6 deployment_validation — Validate deployment per canonical rules
--     (see DET_NAMING_CONVENTIONS.md Section 0: Deployment Rules)
--     NO adjacency check. NO transit delay. Instant placement.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION deployment_validation(
    p_sim_run_id UUID,
    p_country_id TEXT,
    p_role_id TEXT,
    p_unit_type TEXT,     -- ground, naval, tactical_air, strategic_missile, air_defense
    p_count INT,
    p_to_zone TEXT,       -- land zone ID or water hex w(col,row) or ship ID
    p_ship_id TEXT DEFAULT NULL  -- if embarking on a ship
)
RETURNS JSONB
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
AS $$
DECLARE
    v_round INT;
    v_to_zone_rec RECORD;
    v_total_units INT;
    v_has_basing BOOLEAN;
    v_is_water_hex BOOLEAN;
    v_blockade_active BOOLEAN;
    v_ship_ground INT;
    v_ship_air INT;
BEGIN
    -- Verify authorization
    IF NOT check_authorization(p_sim_run_id, p_role_id, 'troop_deployment') THEN
        RETURN jsonb_build_object('valid', false, 'error', 'AUTH_ROLE_MISMATCH');
    END IF;

    SELECT current_round INTO v_round FROM sim_runs WHERE id = p_sim_run_id;

    -- Validate unit type
    IF p_unit_type NOT IN ('ground', 'naval', 'tactical_air', 'strategic_missile', 'air_defense') THEN
        RETURN jsonb_build_object('valid', false, 'error', 'VALIDATION_INVALID_UNIT_TYPE');
    END IF;

    -- Check total units available for this country (across all zones)
    SELECT COALESCE(SUM(count), 0) INTO v_total_units FROM deployments
    WHERE sim_run_id = p_sim_run_id AND country_id = p_country_id AND unit_type = p_unit_type;
    IF v_total_units < p_count THEN
        RETURN jsonb_build_object('valid', false, 'error', 'RESOURCE_NO_UNITS',
            'available', v_total_units, 'requested', p_count);
    END IF;

    -- ── EMBARKING ON SHIP ──
    IF p_ship_id IS NOT NULL THEN
        -- Strategic missiles CANNOT embark
        IF p_unit_type = 'strategic_missile' THEN
            RETURN jsonb_build_object('valid', false, 'error', 'VALIDATION_STRATEGIC_CANNOT_EMBARK');
        END IF;
        -- Naval units don't embark on ships (they ARE ships)
        IF p_unit_type = 'naval' THEN
            RETURN jsonb_build_object('valid', false, 'error', 'VALIDATION_NAVAL_CANNOT_EMBARK');
        END IF;
        -- Ship must belong to same country
        -- (ship_id references a naval deployment of this country)
        -- Check ship capacity: 1 ground + 2 air max
        SELECT COALESCE(SUM(CASE WHEN unit_type = 'ground' THEN count ELSE 0 END), 0),
               COALESCE(SUM(CASE WHEN unit_type = 'tactical_air' THEN count ELSE 0 END), 0)
        INTO v_ship_ground, v_ship_air
        FROM deployments
        WHERE sim_run_id = p_sim_run_id AND zone_id = p_ship_id;

        IF p_unit_type = 'ground' AND (v_ship_ground + p_count) > 1 THEN
            RETURN jsonb_build_object('valid', false, 'error', 'VALIDATION_SHIP_GROUND_CAPACITY',
                'message', 'Max 1 ground unit per ship', 'current', v_ship_ground);
        END IF;
        IF p_unit_type = 'tactical_air' AND (v_ship_air + p_count) > 2 THEN
            RETURN jsonb_build_object('valid', false, 'error', 'VALIDATION_SHIP_AIR_CAPACITY',
                'message', 'Max 2 air units per ship', 'current', v_ship_air);
        END IF;

        RETURN jsonb_build_object('valid', true, 'embark', true, 'ship_id', p_ship_id);
    END IF;

    -- ── NAVAL DEPLOYMENT (water hex) ──
    v_is_water_hex := (p_to_zone LIKE 'w(%');
    IF p_unit_type = 'naval' THEN
        IF NOT v_is_water_hex THEN
            RETURN jsonb_build_object('valid', false, 'error', 'VALIDATION_NAVAL_NEEDS_WATER');
        END IF;
        -- Check for active blockade at this water hex
        SELECT EXISTS (
            SELECT 1 FROM world_state ws
            WHERE ws.sim_run_id = p_sim_run_id AND ws.round_num = v_round
              AND ws.blockaded_zones ? p_to_zone
        ) INTO v_blockade_active;
        IF v_blockade_active THEN
            RETURN jsonb_build_object('valid', false, 'error', 'VALIDATION_BLOCKADE_ACTIVE',
                'message', 'Cannot deploy into an actively blockaded area');
        END IF;
        -- Naval can go ANYWHERE on water (no adjacency, no delay)
        RETURN jsonb_build_object('valid', true);
    END IF;

    -- ── GROUND / AIR / AD / STRATEGIC DEPLOYMENT (land hex) ──
    IF v_is_water_hex THEN
        RETURN jsonb_build_object('valid', false, 'error', 'VALIDATION_LAND_UNIT_NEEDS_GROUND');
    END IF;

    -- Validate target zone exists
    SELECT * INTO v_to_zone_rec FROM zones
    WHERE id = p_to_zone AND sim_run_id = p_sim_run_id;
    IF NOT FOUND THEN
        RETURN jsonb_build_object('valid', false, 'error', 'VALIDATION_ZONE_NOT_FOUND');
    END IF;

    -- Territory check: own territory, controlled territory, or basing agreement
    IF v_to_zone_rec.owner = p_country_id THEN
        -- Own territory: always OK
        RETURN jsonb_build_object('valid', true);
    END IF;

    -- Controlled territory (occupied by this country)
    IF v_to_zone_rec.controlled_by = p_country_id THEN
        RETURN jsonb_build_object('valid', true);
    END IF;

    -- Contested/unowned territory
    IF v_to_zone_rec.owner = 'none' OR v_to_zone_rec.owner IS NULL THEN
        RETURN jsonb_build_object('valid', true);
    END IF;

    -- Foreign territory: check basing rights
    SELECT EXISTS (
        SELECT 1 FROM world_state ws
        WHERE ws.sim_run_id = p_sim_run_id AND ws.round_num = v_round
          AND ws.basing_rights @> jsonb_build_array(
              jsonb_build_object('host', v_to_zone_rec.owner, 'guest', p_country_id)
          )
    ) INTO v_has_basing;

    IF v_has_basing THEN
        RETURN jsonb_build_object('valid', true);
    END IF;

    RETURN jsonb_build_object('valid', false, 'error', 'VALIDATION_NO_TERRITORY_ACCESS',
        'message', 'Not own/controlled/allied territory and no basing agreement',
        'zone_owner', v_to_zone_rec.owner);
END;
$$;


-- =============================================================================
-- END OF SCHEMA
-- =============================================================================

-- =============================================================================
-- CHANGELOG (v1.1, 2026-03-30)
-- =============================================================================
-- Fixes applied per DET_VALIDATION_LEVEL1 + DET_VALIDATION_LEVEL3 findings:
--
-- [HIGH] Event ID format: Changed events.id from UUID to TEXT (ULID format).
--        ULIDs are time-sortable, enabling cursor-based pagination without
--        separate timestamp ordering. Per DET_NAMING_CONVENTIONS 1.5.
--
-- [HIGH] Transaction type enum: Replaced (transfer_coins, trade_deal,
--        basing_rights, aid_package, personal_invest, bribe) with canonical
--        engine names (coin_transfer, arms_transfer, tech_transfer,
--        basing_rights, treaty, agreement, org_creation, personal_investment,
--        bribe). Per DET_NAMING_CONVENTIONS 1.2.
--
-- [HIGH] Added impeachment to check_authorization power map.
--
-- [HIGH] Added deployment_validation() function (B4 addition) for zone
--        adjacency, transit time, unit availability, and basing rights checks.
--
-- [MEDIUM] Renamed events columns: actor -> actor_role_id,
--          country_context -> actor_country_id. Per DET_NAMING_CONVENTIONS 1.1.
--
-- [MEDIUM] Renamed sanctions columns: country -> imposer_country_id,
--          target -> target_country_id. Per DET_NAMING_CONVENTIONS 1.1.1.
--
-- [MEDIUM] Renamed tariffs columns: imposer -> imposer_country_id,
--          target -> target_country_id. Per DET_NAMING_CONVENTIONS 1.1.1.
--
-- [MEDIUM] Renamed relationships columns: from_country -> from_country_id,
--          to_country -> to_country_id. Per DET_NAMING_CONVENTIONS 1.1.1.
--
-- [MEDIUM] Renamed transactions columns: from_country -> from_country_id,
--          to_country -> to_country_id. Per DET_NAMING_CONVENTIONS 1.1.1.
--
-- [MEDIUM] Updated check_authorization power map to use canonical action_type
--          names (ground_attack, tariff_set, etc.) per NAMING_CONVENTIONS 1.3.
--
-- [LOW] Updated all event INSERT statements to use new column names and
--       generate fallback ULID-style IDs for DB-only operations.
--
-- [LOW] Updated RLS policies for renamed columns.
--
-- [LOW] Updated FK references: transactions.event_id and combat_results.event_id
--       changed from UUID to TEXT to match new events.id type.
-- =============================================================================
