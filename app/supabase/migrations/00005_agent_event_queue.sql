-- Migration: agent_event_queue
-- Unified event queue for AI agent event delivery.
-- All game events (chat, attacks, meetings, round updates) flow through this queue.
-- The EventDispatcher reads from this table and delivers to idle agents.

CREATE TABLE agent_event_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sim_run_id UUID NOT NULL,
    role_id TEXT NOT NULL,
    tier INTEGER NOT NULL CHECK (tier IN (1, 2, 3)),
    event_type TEXT NOT NULL,
    message TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now(),
    processed_at TIMESTAMPTZ,
    processing_error TEXT
);

CREATE INDEX idx_aeq_pending ON agent_event_queue(sim_run_id, role_id, tier)
    WHERE processed_at IS NULL;
CREATE INDEX idx_aeq_sim ON agent_event_queue(sim_run_id);

-- RLS
ALTER TABLE agent_event_queue ENABLE ROW LEVEL SECURITY;
CREATE POLICY "service_role_full_aeq" ON agent_event_queue FOR ALL TO service_role USING (true);
CREATE POLICY "authenticated_read_aeq" ON agent_event_queue FOR SELECT TO authenticated USING (true);
