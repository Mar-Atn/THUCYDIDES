-- =============================================================================
-- DET_B1_SCHEMA_ADDENDUM_BUILD.sql
-- Tables added during BUILD phase (Sprint A+B) — not yet in DET_B1 v1.2
-- Version: 1.0 | Date: 2026-04-13
-- Source: engine/services/*.py code + Supabase migrations
--
-- This file documents 26 tables used by production code that are NOT
-- in the original DET_B1_DATABASE_SCHEMA.sql (v1.2, 2026-04-03).
-- Once reconciled, these should be merged into DET_B1 v1.3.
-- =============================================================================

-- =============================================================================
-- SECTION A: TEMPLATE / SCENARIO / RUN HIERARCHY
-- =============================================================================

-- Supersedes: None (new concept from F1 sprint)
CREATE TABLE sim_templates (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code            TEXT UNIQUE NOT NULL,     -- e.g. 'ttt_v1'
    name            TEXT NOT NULL,
    version         TEXT NOT NULL DEFAULT '1.0',
    description     TEXT,
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE sim_scenarios (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id     UUID REFERENCES sim_templates(id),
    code            TEXT UNIQUE NOT NULL,     -- e.g. 'start_one'
    name            TEXT NOT NULL,
    config          JSONB DEFAULT '{}',       -- sparse overrides of template
    created_at      TIMESTAMPTZ DEFAULT now()
);

-- sim_runs already in DET_B1 but needs these columns:
-- ALTER TABLE sim_runs ADD COLUMN scenario_id UUID REFERENCES sim_scenarios(id);
-- ALTER TABLE sim_runs ADD COLUMN description TEXT;
-- ALTER TABLE sim_runs ADD COLUMN seed JSONB;
-- ALTER TABLE sim_runs ADD COLUMN finalized_at TIMESTAMPTZ;

-- =============================================================================
-- SECTION B: PER-ROUND STATE SNAPSHOTS (supersede DET_B1 country_state etc.)
-- =============================================================================

-- Supersedes: country_state (DET_B1)
-- Key change: keyed by sim_run_id (not scenario_id), immutable per round
CREATE TABLE country_states_per_round (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sim_run_id              UUID NOT NULL REFERENCES sim_runs(id) ON DELETE CASCADE,
    round_num               INT NOT NULL,
    country_code            TEXT NOT NULL,
    -- Economic
    gdp                     FLOAT,
    gdp_growth_rate         FLOAT,
    treasury                FLOAT,
    inflation               FLOAT,
    debt_burden             FLOAT,
    economic_state          TEXT DEFAULT 'normal',
    sanctions_coefficient   FLOAT DEFAULT 1.0,
    tariff_coefficient      FLOAT DEFAULT 1.0,
    -- Political
    stability               INT DEFAULT 5,
    political_support       INT DEFAULT 50,
    war_tiredness           INT DEFAULT 0,
    -- Technology
    nuclear_level           INT DEFAULT 0,
    nuclear_rd_progress     FLOAT DEFAULT 0,
    ai_level                INT DEFAULT 0,
    ai_rd_progress          FLOAT DEFAULT 0,
    -- Military (aggregate counts)
    military                JSONB DEFAULT '{}',
    -- Flags
    martial_law_declared    BOOLEAN NOT NULL DEFAULT false,
    early_election_called   BOOLEAN NOT NULL DEFAULT false,
    -- Audit JSONB columns (one per action engine)
    budget_result           JSONB,
    sanctions_result        JSONB,
    tariff_result           JSONB,
    opec_result             JSONB,
    combat_result           JSONB,
    movement_result         JSONB,
    arrest_result           JSONB,
    propaganda_result       JSONB,
    sabotage_result         JSONB,
    election_meddling_result JSONB,
    assassination_result    JSONB,
    coup_result             JSONB,
    UNIQUE(sim_run_id, round_num, country_code)
);

-- Supersedes: world_state snapshots
CREATE TABLE global_state_per_round (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sim_run_id      UUID NOT NULL REFERENCES sim_runs(id) ON DELETE CASCADE,
    round_num       INT NOT NULL,
    oil_price       FLOAT,
    market_indexes  JSONB,
    wars            JSONB DEFAULT '[]',
    active_blockades JSONB DEFAULT '{}',
    chokepoint_status JSONB DEFAULT '{}',
    opec_production JSONB DEFAULT '{}',
    UNIQUE(sim_run_id, round_num)
);

CREATE TABLE unit_states_per_round (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sim_run_id      UUID NOT NULL REFERENCES sim_runs(id) ON DELETE CASCADE,
    round_num       INT NOT NULL,
    unit_code       TEXT NOT NULL,
    country_code    TEXT NOT NULL,
    unit_type       TEXT NOT NULL,
    status          TEXT DEFAULT 'active',
    global_row      INT,
    global_col      INT,
    theater         TEXT,
    theater_row     INT,
    theater_col     INT,
    embarked_on     TEXT,
    UNIQUE(sim_run_id, round_num, unit_code)
);

-- =============================================================================
-- SECTION C: RUN ROLES (supersedes DET_B1 role_state)
-- =============================================================================

CREATE TABLE run_roles (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sim_run_id      UUID NOT NULL REFERENCES sim_runs(id) ON DELETE CASCADE,
    role_id         TEXT NOT NULL,
    character_name  TEXT,
    country_code    TEXT NOT NULL,
    title           TEXT,
    is_head_of_state BOOLEAN DEFAULT false,
    is_military_chief BOOLEAN DEFAULT false,
    status          TEXT DEFAULT 'active',    -- active|arrested|killed|deposed
    personal_coins  INT DEFAULT 0,
    status_changed_by TEXT,
    status_reason   TEXT,
    status_changed_round INT,
    UNIQUE(sim_run_id, role_id)
);

-- =============================================================================
-- SECTION D: POWER ASSIGNMENTS
-- =============================================================================

CREATE TABLE power_assignments (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sim_run_id      UUID NOT NULL REFERENCES sim_runs(id) ON DELETE CASCADE,
    country_code    TEXT NOT NULL,
    power_type      TEXT NOT NULL,            -- military|economic|foreign_affairs
    assigned_role_id TEXT NOT NULL,
    assigned_by     TEXT,
    assigned_at     TIMESTAMPTZ DEFAULT now(),
    UNIQUE(sim_run_id, country_code, power_type)
);

-- =============================================================================
-- SECTION E: ELECTIONS
-- =============================================================================

CREATE TABLE election_nominations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sim_run_id      UUID NOT NULL REFERENCES sim_runs(id) ON DELETE CASCADE,
    election_type   TEXT NOT NULL,
    election_round  INT NOT NULL,
    role_id         TEXT NOT NULL,
    country_code    TEXT NOT NULL DEFAULT 'columbia',
    camp            TEXT NOT NULL DEFAULT 'unknown',
    nominated_at    TIMESTAMPTZ DEFAULT now(),
    UNIQUE(sim_run_id, election_type, role_id)
);

CREATE TABLE election_votes (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sim_run_id      UUID NOT NULL REFERENCES sim_runs(id) ON DELETE CASCADE,
    election_type   TEXT NOT NULL,
    election_round  INT NOT NULL,
    voter_role_id   TEXT NOT NULL,
    candidate_role_id TEXT NOT NULL,
    country_code    TEXT NOT NULL DEFAULT 'columbia',
    voted_at        TIMESTAMPTZ DEFAULT now(),
    UNIQUE(sim_run_id, election_type, voter_role_id)
);

CREATE TABLE election_results (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sim_run_id      UUID NOT NULL REFERENCES sim_runs(id) ON DELETE CASCADE,
    election_type   TEXT NOT NULL,
    election_round  INT NOT NULL,
    country_code    TEXT NOT NULL DEFAULT 'columbia',
    winner_role_id  TEXT NOT NULL,
    ai_score        FLOAT NOT NULL,
    participant_votes JSONB NOT NULL DEFAULT '{}',
    population_votes JSONB NOT NULL DEFAULT '{}',
    total_votes     JSONB NOT NULL DEFAULT '{}',
    seat_changed    TEXT,
    resolved_at     TIMESTAMPTZ DEFAULT now(),
    UNIQUE(sim_run_id, election_type)
);

-- =============================================================================
-- SECTION F: NUCLEAR ACTIONS
-- =============================================================================

CREATE TABLE nuclear_actions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sim_run_id      UUID NOT NULL REFERENCES sim_runs(id) ON DELETE CASCADE,
    round_num       INT NOT NULL,
    phase           TEXT NOT NULL,            -- initiate|authorize|alert|resolve
    launcher_country TEXT NOT NULL,
    target_countries JSONB DEFAULT '[]',
    missiles        JSONB DEFAULT '[]',
    authorization   JSONB,
    interception    JSONB,
    resolution      JSONB,
    status          TEXT DEFAULT 'pending',
    created_at      TIMESTAMPTZ DEFAULT now(),
    resolved_at     TIMESTAMPTZ
);

-- =============================================================================
-- SECTION G: TRANSACTIONS & AGREEMENTS
-- =============================================================================

CREATE TABLE exchange_transactions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sim_run_id      UUID NOT NULL REFERENCES sim_runs(id) ON DELETE CASCADE,
    round_num       INT NOT NULL,
    proposer_role   TEXT NOT NULL,
    proposer_country TEXT NOT NULL,
    counterpart_role TEXT,
    counterpart_country TEXT NOT NULL,
    offer           JSONB DEFAULT '{}',
    request         JSONB DEFAULT '{}',
    status          TEXT DEFAULT 'pending',   -- pending|accepted|declined|countered|executed
    counter_offer   JSONB,
    created_at      TIMESTAMPTZ DEFAULT now(),
    resolved_at     TIMESTAMPTZ
);

CREATE TABLE agreements (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sim_run_id      UUID NOT NULL REFERENCES sim_runs(id) ON DELETE CASCADE,
    round_num       INT NOT NULL,
    agreement_type  TEXT NOT NULL,
    name            TEXT,
    proposer_role   TEXT NOT NULL,
    proposer_country TEXT NOT NULL,
    terms           JSONB DEFAULT '{}',
    visibility      TEXT DEFAULT 'public',
    signatures      JSONB DEFAULT '{}',       -- {role_id: {signed_at, round_num}}
    status          TEXT DEFAULT 'proposed',  -- proposed|active|expired
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE basing_rights (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sim_run_id      UUID NOT NULL REFERENCES sim_runs(id) ON DELETE CASCADE,
    host_country    TEXT NOT NULL,
    guest_country   TEXT NOT NULL,
    zone_id         TEXT NOT NULL,
    granted_by      TEXT,
    granted_round   INT,
    status          TEXT DEFAULT 'active',
    UNIQUE(sim_run_id, host_country, guest_country, zone_id)
);

-- =============================================================================
-- SECTION H: OBSERVATORY
-- =============================================================================

CREATE TABLE observatory_events (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sim_run_id      UUID NOT NULL REFERENCES sim_runs(id) ON DELETE CASCADE,
    scenario_id     UUID,
    round_num       INT NOT NULL,
    event_type      TEXT NOT NULL,
    country_code    TEXT,
    summary         TEXT,
    payload         JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE observatory_combat_results (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sim_run_id      UUID NOT NULL REFERENCES sim_runs(id) ON DELETE CASCADE,
    scenario_id     UUID,
    round_num       INT NOT NULL,
    combat_type     TEXT NOT NULL,
    attacker_country TEXT NOT NULL,
    defender_country TEXT NOT NULL,
    attacker_rolls  JSONB,                    -- migrated from int[] to jsonb
    defender_rolls  JSONB,                    -- migrated from int[] to jsonb
    modifier_breakdown JSONB,
    result_summary  JSONB,
    created_at      TIMESTAMPTZ DEFAULT now()
);

-- =============================================================================
-- SECTION I: AI AGENT TABLES
-- =============================================================================

CREATE TABLE agent_decisions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sim_run_id      UUID REFERENCES sim_runs(id) ON DELETE CASCADE,
    scenario_id     UUID,
    country_code    TEXT,
    action_type     TEXT NOT NULL,
    action_payload  JSONB DEFAULT '{}',
    rationale       TEXT,
    validation_status TEXT,
    validation_notes TEXT,
    round_num       INT,
    processed_at    TIMESTAMPTZ,              -- set when action_dispatcher processes it
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE agent_memories (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sim_run_id      UUID NOT NULL REFERENCES sim_runs(id) ON DELETE CASCADE,
    country_code    TEXT NOT NULL,
    memory_key      TEXT NOT NULL,
    content         TEXT,
    round_num       INT,
    updated_at      TIMESTAMPTZ DEFAULT now(),
    UNIQUE(sim_run_id, country_code, memory_key)
);

CREATE TABLE agent_reflections (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sim_run_id      UUID NOT NULL REFERENCES sim_runs(id) ON DELETE CASCADE,
    country_code    TEXT NOT NULL,
    round_num       INT NOT NULL,
    reflection      TEXT,
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE agent_conversations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sim_run_id      UUID NOT NULL REFERENCES sim_runs(id) ON DELETE CASCADE,
    round_num       INT,
    participants    JSONB DEFAULT '[]',
    topic           TEXT,
    messages        JSONB DEFAULT '[]',
    status          TEXT DEFAULT 'active',
    created_at      TIMESTAMPTZ DEFAULT now()
);

-- =============================================================================
-- SECTION J: LAYOUT / TEMPLATE DATA
-- =============================================================================

CREATE TABLE unit_layouts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    layout_code     TEXT UNIQUE NOT NULL,
    name            TEXT,
    description     TEXT,
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE layout_units (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    layout_id       UUID REFERENCES unit_layouts(id),
    unit_code       TEXT NOT NULL,
    country_code    TEXT NOT NULL,
    unit_type       TEXT NOT NULL,
    global_row      INT,
    global_col      INT,
    theater         TEXT,
    theater_row     INT,
    theater_col     INT,
    embarked_on     TEXT,
    status          TEXT DEFAULT 'active'
);

-- =============================================================================
-- END OF ADDENDUM
-- When reconciling into DET_B1 v1.3:
-- 1. Replace country_state with country_states_per_round
-- 2. Replace role_state with run_roles
-- 3. Replace events with observatory_events
-- 4. Replace transactions with exchange_transactions
-- 5. Replace combat_results with observatory_combat_results
-- 6. Remove argus_* tables (replaced by agent_* tables)
-- 7. Add all new tables from sections D-J
-- =============================================================================
