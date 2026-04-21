-- ============================================================================
-- TTT Meetings Module — meetings + meeting_messages tables
-- Migration: 00002_create_meetings_and_messages
-- Date: 2026-04-21
-- ============================================================================

-- --------------------------------------------------------------------------
-- 1. Meetings table — chat channel record (created when invitation accepted)
-- --------------------------------------------------------------------------
CREATE TABLE meetings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sim_run_id UUID NOT NULL,
    invitation_id UUID,
    round_num INTEGER,
    status TEXT CHECK (status IN ('active', 'completed', 'abandoned')) DEFAULT 'active',
    participant_a_role_id TEXT NOT NULL,
    participant_a_country TEXT NOT NULL,
    participant_b_role_id TEXT NOT NULL,
    participant_b_country TEXT NOT NULL,
    agenda TEXT,
    modality TEXT CHECK (modality IN ('text', 'voice', 'hybrid')) DEFAULT 'text',
    turn_count INTEGER DEFAULT 0,
    max_turns INTEGER DEFAULT 16,
    started_at TIMESTAMPTZ DEFAULT now(),
    ended_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}'
);

-- --------------------------------------------------------------------------
-- 2. Meeting messages table — turn-by-turn message persistence
-- --------------------------------------------------------------------------
CREATE TABLE meeting_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    meeting_id UUID REFERENCES meetings(id) ON DELETE CASCADE,
    role_id TEXT NOT NULL,
    country_code TEXT NOT NULL,
    content TEXT NOT NULL,
    channel TEXT CHECK (channel IN ('text', 'voice', 'system')) DEFAULT 'text',
    turn_number INTEGER,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- --------------------------------------------------------------------------
-- 3. Enable realtime for meeting_messages
-- --------------------------------------------------------------------------
ALTER PUBLICATION supabase_realtime ADD TABLE meetings;
ALTER PUBLICATION supabase_realtime ADD TABLE meeting_messages;

-- --------------------------------------------------------------------------
-- 4. Indexes
-- --------------------------------------------------------------------------
CREATE INDEX idx_meetings_sim_run ON meetings(sim_run_id);
CREATE INDEX idx_meetings_status ON meetings(status);
CREATE INDEX idx_meetings_participants ON meetings(participant_a_role_id, participant_b_role_id);
CREATE INDEX idx_meeting_messages_meeting ON meeting_messages(meeting_id);
CREATE INDEX idx_meeting_messages_created ON meeting_messages(meeting_id, created_at);
