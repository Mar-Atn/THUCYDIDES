-- Migration: Create ai_agent_sessions table
-- Tracks active managed agent sessions for M5 AI Participants.
-- Each row = one Claude Managed Agent session bound to a sim_run + role.

CREATE TABLE IF NOT EXISTS ai_agent_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sim_run_id UUID NOT NULL,
    role_id TEXT NOT NULL,
    country_code TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    environment_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    status TEXT CHECK (status IN (
        'initializing', 'ready', 'active', 'frozen', 'terminated', 'archived'
    )) DEFAULT 'initializing',
    model TEXT DEFAULT 'claude-sonnet-4-6',
    round_num INTEGER DEFAULT 1,
    total_input_tokens BIGINT DEFAULT 0,
    total_output_tokens BIGINT DEFAULT 0,
    events_sent INTEGER DEFAULT 0,
    actions_submitted INTEGER DEFAULT 0,
    tool_calls INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now(),
    last_active_at TIMESTAMPTZ DEFAULT now(),
    metadata JSONB DEFAULT '{}',
    UNIQUE(sim_run_id, role_id)
);

CREATE INDEX IF NOT EXISTS idx_ai_sessions_sim ON ai_agent_sessions(sim_run_id);
CREATE INDEX IF NOT EXISTS idx_ai_sessions_status ON ai_agent_sessions(status);
