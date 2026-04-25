/**
 * AgentDetailPage — full-page view of a single AI agent's state, activities,
 * decisions, meetings, and memory.
 *
 * Route: /sim/:simId/agent/:roleId
 * Navigated from AIParticipantDashboard agent row click.
 *
 * Spec: MODULES/M5_AI_PARTICIPANT/SPEC_M5_AI_PARTICIPANT.md (D9, Level 2)
 */

import { useEffect, useState, useCallback, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { supabase } from '@/lib/supabase'
import {
  getSimRunRoles,
  getAIStatus,
  freezeAgent,
  resumeAgent,
  type SimRunRole,
  type AIAgentStatus,
  type AgentLogEntry,
  type AgentMemory,
} from '@/lib/queries'

/* -------------------------------------------------------------------------- */
/*  Constants                                                                  */
/* -------------------------------------------------------------------------- */

const POLL_INTERVAL_MS = 5000

const STATE_COLORS: Record<string, { dot: string; badge: string }> = {
  INITIALIZING: { dot: 'bg-action animate-pulse', badge: 'bg-action/10 text-action' },
  IDLE:         { dot: 'bg-success',              badge: 'bg-success/10 text-success' },
  THINKING:     { dot: 'bg-action',               badge: 'bg-action/10 text-action' },
  ACTING:       { dot: 'bg-warning',              badge: 'bg-warning/10 text-warning' },
  IN_MEETING:   { dot: 'bg-accent',               badge: 'bg-accent/10 text-accent' },
  FROZEN:       { dot: 'bg-text-secondary',        badge: 'bg-text-secondary/10 text-text-secondary' },
  TERMINATED:   { dot: 'bg-danger',               badge: 'bg-danger/10 text-danger' },
}

const DEFAULT_STYLE = { dot: 'bg-text-secondary/30', badge: 'bg-text-secondary/10 text-text-secondary' }

function stateStyle(state: string) {
  return STATE_COLORS[state] ?? DEFAULT_STYLE
}

/* -------------------------------------------------------------------------- */
/*  Types (local to this page)                                                 */
/* -------------------------------------------------------------------------- */

interface AgentSession {
  id: string
  sim_run_id: string
  role_id: string
  country_code: string
  status: string
  model: string | null
  total_input_tokens: number
  total_output_tokens: number
  total_cost_usd: number
  events_sent: number
  actions_submitted: number
  tool_calls: number
  environment_id: string | null
  created_at: string
  last_active_at: string | null
}

interface AgentDecision {
  id: string
  sim_run_id: string
  round_num: number
  action_type: string
  country_code: string
  action_payload: Record<string, unknown> | null
  validation_status: string
  validation_notes: string | null
  rationale: string | null
  created_at: string
}

interface Meeting {
  id: string
  sim_run_id: string
  round_num: number
  status: string
  participant_a_role_id: string
  participant_b_role_id: string
  created_at: string
  completed_at: string | null
}

interface MeetingMessage {
  id: string
  meeting_id: string
  role_id: string
  content: string
  turn_number: number
  created_at: string
}

/* -------------------------------------------------------------------------- */
/*  Activity Descriptor (reused from dashboard)                                */
/* -------------------------------------------------------------------------- */

function getActivityDescriptor(entry: AgentLogEntry): string {
  const cat = entry.category ?? ''
  const sum = (entry.summary || '').toLowerCase()

  if (cat === 'agent_tool_call') {
    if (sum.includes('get_my_country')) return 'Checking own status'
    if (sum.includes('get_my_forces')) return 'Reviewing forces'
    if (sum.includes('get_relationships')) return 'Checking relationships'
    if (sum.includes('get_my_artefacts')) return 'Reading intel'
    if (sum.includes('get_recent_events')) return 'Scanning events'
    if (sum.includes('get_country_info')) return 'Looking up country'
    if (sum.includes('get_hex_info')) return 'Checking map position'
    if (sum.includes('get_pending_proposals')) return 'Reviewing proposals'
    if (sum.includes('get_action_rules')) return 'Checking action rules'
    if (sum.includes('get_organizations')) return 'Checking organizations'
    if (sum.includes('read_notes') || sum.includes('list_my_memories')) return 'Reading notes'
    if (sum.includes('write_notes') || sum.includes('write_memory')) return 'Writing notes'
    if (sum.includes('request_meeting')) return 'Requesting meeting'
    if (sum.includes('respond_to_invitation')) return 'Responding to invitation'
    if (sum.includes('submit_action') || sum.includes('commit_action')) return 'Submitting action'
    return 'Using tool'
  }

  if (cat === 'agent_reasoning') return 'Analyzing situation'
  return 'Event'
}

/* -------------------------------------------------------------------------- */
/*  Log type color helper                                                      */
/* -------------------------------------------------------------------------- */

function logTypeColor(logType: string): string {
  switch (logType.toLowerCase()) {
    case 'action':
      return 'text-success'
    case 'tool':
    case 'tool_call':
    case 'agent_tool_call':
      return 'text-action'
    case 'reasoning':
    case 'thought':
    case 'agent_reasoning':
      return 'text-accent'
    case 'meeting':
    case 'conversation':
      return 'text-warning'
    case 'error':
      return 'text-danger'
    default:
      return 'text-text-secondary'
  }
}

/* -------------------------------------------------------------------------- */
/*  Collapsible Section                                                        */
/* -------------------------------------------------------------------------- */

function Section({
  title,
  count,
  defaultOpen = true,
  children,
}: {
  title: string
  count?: number
  defaultOpen?: boolean
  children: React.ReactNode
}) {
  const [open, setOpen] = useState(defaultOpen)
  return (
    <section className="bg-card border border-border rounded-lg">
      <button
        onClick={() => setOpen(!open)}
        className="w-full px-5 py-3 flex items-center justify-between hover:bg-base/50 transition-colors rounded-t-lg"
      >
        <div className="flex items-center gap-2">
          <span className="font-body text-caption text-text-secondary">
            {open ? '\u25BE' : '\u25B8'}
          </span>
          <h3 className="font-heading text-h3 text-text-primary">{title}</h3>
          {count !== undefined && (
            <span className="font-data text-caption bg-action/10 text-action px-2 py-0.5 rounded-full">
              {count}
            </span>
          )}
        </div>
      </button>
      {open && <div className="px-5 pb-4">{children}</div>}
    </section>
  )
}

/* -------------------------------------------------------------------------- */
/*  Main Page Component                                                        */
/* -------------------------------------------------------------------------- */

export function AgentDetailPage() {
  const { simId, roleId } = useParams<{ simId: string; roleId: string }>()
  const navigate = useNavigate()

  /* State */
  const [role, setRole] = useState<SimRunRole | null>(null)
  const [orchAgent, setOrchAgent] = useState<AIAgentStatus | null>(null)
  const [session, setSession] = useState<AgentSession | null>(null)
  const [logEntries, setLogEntries] = useState<AgentLogEntry[]>([])
  const [memories, setMemories] = useState<AgentMemory[]>([])
  const [decisions, setDecisions] = useState<AgentDecision[]>([])
  const [meetings, setMeetings] = useState<Meeting[]>([])
  const [meetingMessages, setMeetingMessages] = useState<Record<string, MeetingMessage[]>>({})
  const [allRoles, setAllRoles] = useState<SimRunRole[]>([])

  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)
  const [expandedLogs, setExpandedLogs] = useState<Set<string>>(new Set())
  const [expandedMemories, setExpandedMemories] = useState<Set<string>>(new Set())
  const [expandedDecisions, setExpandedDecisions] = useState<Set<string>>(new Set())
  const [expandedMeetings, setExpandedMeetings] = useState<Set<string>>(new Set())

  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  /* ── Initial role fetch ──────────────────────────────────────────────── */
  useEffect(() => {
    if (!simId) return
    getSimRunRoles(simId).then((roles) => {
      setAllRoles(roles)
      const found = roles.find((r) => r.id === roleId)
      setRole(found ?? null)
    }).catch(() => {})
  }, [simId, roleId])

  /* ── Poll all data ───────────────────────────────────────────────────── */
  const fetchAll = useCallback(async () => {
    if (!simId || !roleId || !role) return

    try {
      /* Orchestrator status for this agent */
      const aiStatus = await getAIStatus(simId).catch(() => null)
      if (aiStatus) {
        const agent = aiStatus.agents.find((a) => a.role_id === roleId)
        setOrchAgent(agent ?? null)
      }

      /* DB session */
      const { data: sessionData } = await supabase
        .from('ai_agent_sessions')
        .select('*')
        .eq('sim_run_id', simId)
        .eq('role_id', roleId)
        .order('created_at', { ascending: false })
        .limit(1)
        .single()
      if (sessionData) setSession(sessionData as AgentSession)

      /* Activity log from observatory_events */
      const { data: logs } = await supabase
        .from('observatory_events')
        .select('id, sim_run_id, round_num, event_type, country_code, summary, payload, phase, category, role_name, created_at')
        .eq('sim_run_id', simId)
        .eq('event_type', 'ai_agent_log')
        .eq('country_code', role.country_code)
        .order('created_at', { ascending: false })
        .limit(200)
      if (logs) setLogEntries(logs as AgentLogEntry[])

      /* Memories */
      const { data: memData } = await supabase
        .from('agent_memories')
        .select('*')
        .eq('sim_run_id', simId)
        .eq('country_code', role.country_code)
        .order('round_num', { ascending: false })
      if (memData) setMemories(memData as AgentMemory[])

      /* Decisions */
      const { data: decData } = await supabase
        .from('agent_decisions')
        .select('*')
        .eq('sim_run_id', simId)
        .eq('country_code', role.country_code)
        .order('created_at', { ascending: false })
      if (decData) setDecisions(decData as AgentDecision[])

      /* Meetings — where this role is initiator or invitee */
      const { data: mtgData } = await supabase
        .from('meetings')
        .select('*')
        .eq('sim_run_id', simId)
        .or(`participant_a_role_id.eq.${roleId},participant_b_role_id.eq.${roleId}`)
        .order('started_at', { ascending: false })
      if (mtgData) setMeetings(mtgData as Meeting[])
    } catch {
      /* non-critical */
    } finally {
      setLoading(false)
    }
  }, [simId, roleId, role])

  useEffect(() => {
    fetchAll()
    pollRef.current = setInterval(fetchAll, POLL_INTERVAL_MS)
    return () => {
      if (pollRef.current) clearInterval(pollRef.current)
    }
  }, [fetchAll])

  /* ── Meeting messages (on-demand) ────────────────────────────────────── */
  const loadMeetingMessages = useCallback(async (meetingId: string) => {
    const { data } = await supabase
      .from('meeting_messages')
      .select('*')
      .eq('meeting_id', meetingId)
      .order('turn_number', { ascending: true })
    if (data) {
      setMeetingMessages((prev) => ({ ...prev, [meetingId]: data as MeetingMessage[] }))
    }
  }, [])

  /* ── Freeze / Resume ─────────────────────────────────────────────────── */
  const handleFreeze = async () => {
    if (!simId || !roleId) return
    setActionLoading(true)
    try { await freezeAgent(simId, roleId) } catch { /* */ }
    finally { setActionLoading(false); fetchAll() }
  }

  const handleResume = async () => {
    if (!simId || !roleId) return
    setActionLoading(true)
    try { await resumeAgent(simId, roleId) } catch { /* */ }
    finally { setActionLoading(false); fetchAll() }
  }

  /* ── Expand/collapse helpers ─────────────────────────────────────────── */
  const toggleLog = (id: string) => {
    setExpandedLogs((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id); else next.add(id)
      return next
    })
  }

  const toggleMemory = (id: string) => {
    setExpandedMemories((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id); else next.add(id)
      return next
    })
  }

  const toggleDecision = (id: string) => {
    setExpandedDecisions((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id); else next.add(id)
      return next
    })
  }

  const toggleMeeting = (id: string) => {
    setExpandedMeetings((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id); else next.add(id)
      return next
    })
    if (!meetingMessages[id]) {
      loadMeetingMessages(id)
    }
  }

  /* ── Role lookup helper ──────────────────────────────────────────────── */
  const roleMap = new Map(allRoles.map((r) => [r.id, r]))
  const getRoleName = (id: string) => roleMap.get(id)?.character_name ?? id.slice(0, 12)

  /* ── Derived state ───────────────────────────────────────────────────── */
  const agentState = orchAgent?.state ?? session?.status?.toUpperCase() ?? 'UNKNOWN'
  const style = stateStyle(agentState)
  const isFrozen = agentState === 'FROZEN'

  const tokenOut = orchAgent?.cost.output_tokens ?? session?.total_output_tokens ?? 0
  const costUsd = orchAgent?.cost.total_cost_usd ?? session?.total_cost_usd ?? 0
  const eventsSent = orchAgent?.cost.events_sent ?? session?.events_sent ?? 0
  const model = orchAgent?.cost.model ?? session?.model ?? 'unknown'
  const sessionId = orchAgent?.session_id ?? session?.id ?? 'N/A'
  const roundNum = orchAgent?.round_num ?? 0

  /* ── Loading / Error states ──────────────────────────────────────────── */
  if (loading && !role) {
    return (
      <div className="min-h-screen bg-base flex items-center justify-center">
        <p className="font-body text-body text-text-secondary">Loading agent detail...</p>
      </div>
    )
  }

  if (!role) {
    return (
      <div className="min-h-screen bg-base flex flex-col items-center justify-center gap-4">
        <p className="font-body text-body text-text-secondary">Role not found: {roleId}</p>
        <button
          onClick={() => navigate(`/sim/${simId}/live`)}
          className="font-body text-body-sm text-action hover:underline"
        >
          Back to Dashboard
        </button>
      </div>
    )
  }

  /* ── RENDER ──────────────────────────────────────────────────────────── */
  return (
    <div className="min-h-screen bg-base">
      {/* ── Header ─────────────────────────────────────────────────────── */}
      <header className="bg-card border-b border-border sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-4">
          {/* Back link */}
          <button
            onClick={() => navigate(`/sim/${simId}/live`)}
            className="font-body text-body-sm text-action hover:underline mb-2 flex items-center gap-1"
          >
            <span>&larr;</span> Back to Dashboard
          </button>

          {/* Name + State */}
          <div className="flex items-center justify-between flex-wrap gap-3">
            <div className="flex items-center gap-3">
              <span className={`w-3 h-3 rounded-full ${style.dot}`} />
              <h1 className="font-heading text-h2 text-text-primary">
                {role.character_name}
              </h1>
              <span className="font-body text-body text-text-secondary">
                {role.title} of {role.country_code}
              </span>
              <span className={`font-data text-caption px-2 py-0.5 rounded ${style.badge}`}>
                {agentState}
              </span>
            </div>

            {/* Controls */}
            <div className="flex items-center gap-3">
              <button
                onClick={isFrozen ? handleResume : handleFreeze}
                disabled={actionLoading}
                className={`font-body text-body-sm font-medium px-4 py-1.5 rounded transition-colors disabled:opacity-40 ${
                  isFrozen
                    ? 'bg-success/10 text-success hover:bg-success/20'
                    : 'bg-text-secondary/10 text-text-secondary hover:bg-text-secondary/20'
                }`}
              >
                {actionLoading ? '...' : isFrozen ? 'Resume' : 'Freeze'}
              </button>
            </div>
          </div>

          {/* Stats row */}
          <div className="flex flex-wrap gap-4 mt-2 font-data text-caption text-text-secondary">
            <span>Session: {sessionId.slice(0, 12)}...</span>
            <span>Model: {model}</span>
            <span>Round {roundNum}</span>
            <span>Tokens: {tokenOut.toLocaleString()} out</span>
            <span>Cost: ${costUsd.toFixed(4)}</span>
            <span>Events: {eventsSent}</span>
          </div>
        </div>
      </header>

      {/* ── Content ────────────────────────────────────────────────────── */}
      <main className="max-w-7xl mx-auto px-6 py-6 space-y-6">

        {/* Section 1: Activity Log */}
        <Section title="Activity Log" count={logEntries.length}>
          {logEntries.length === 0 ? (
            <p className="font-body text-caption text-text-secondary">No activity recorded yet.</p>
          ) : (
            <div className="space-y-1 max-h-[600px] overflow-y-auto">
              {logEntries.map((entry) => {
                const isExpanded = expandedLogs.has(entry.id)
                const time = new Date(entry.created_at).toLocaleTimeString([], {
                  hour: '2-digit',
                  minute: '2-digit',
                  second: '2-digit',
                })
                const payload = entry.payload ?? {}
                const logType = entry.category ?? 'event'
                const detail = (payload.detail as string) ?? (payload.rationale as string) ?? ''
                const descriptor = getActivityDescriptor(entry)

                return (
                  <div
                    key={entry.id}
                    className="cursor-pointer hover:bg-base/50 rounded px-2 py-1.5 transition-colors"
                    onClick={() => toggleLog(entry.id)}
                  >
                    <div className="flex items-center gap-2">
                      <span className="font-body text-caption text-text-secondary flex-shrink-0">
                        {isExpanded ? '\u25BE' : '\u25B8'}
                      </span>
                      <span className="font-data text-caption text-text-secondary flex-shrink-0 w-20">
                        {time}
                      </span>
                      <span className={`font-data text-caption font-medium flex-shrink-0 w-28 ${logTypeColor(logType)}`}>
                        {descriptor}
                      </span>
                      <span className="font-body text-caption text-text-primary truncate">
                        {entry.summary}
                      </span>
                      <span className="font-data text-caption text-text-secondary flex-shrink-0 ml-auto">
                        R{entry.round_num}
                      </span>
                    </div>
                    {isExpanded && (
                      <div className="ml-8 mt-2 space-y-1">
                        {detail && (
                          <p className="font-body text-caption text-text-secondary italic whitespace-pre-wrap">
                            {detail}
                          </p>
                        )}
                        {Object.keys(payload).length > 0 && (
                          <pre className="font-data text-caption text-text-secondary whitespace-pre-wrap bg-base border border-border rounded p-2 max-h-48 overflow-y-auto">
                            {JSON.stringify(payload, null, 2)}
                          </pre>
                        )}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </Section>

        {/* Section 2: Meetings */}
        <Section title="Meetings" count={meetings.length} defaultOpen={meetings.length > 0}>
          {meetings.length === 0 ? (
            <p className="font-body text-caption text-text-secondary">No meetings yet.</p>
          ) : (
            <div className="space-y-2">
              {meetings.map((mtg) => {
                const isExpanded = expandedMeetings.has(mtg.id)
                const isActive = mtg.status === 'active' || mtg.status === 'in_progress'
                const counterpartId = mtg.participant_a_role_id === roleId
                  ? mtg.participant_b_role_id
                  : mtg.participant_a_role_id
                const counterpart = getRoleName(counterpartId)
                const msgs = meetingMessages[mtg.id] ?? []

                return (
                  <div
                    key={mtg.id}
                    className={`border rounded-lg transition-colors ${
                      isActive ? 'border-accent bg-accent/5' : 'border-border'
                    }`}
                  >
                    <button
                      onClick={() => toggleMeeting(mtg.id)}
                      className="w-full px-4 py-2.5 flex items-center justify-between hover:bg-base/50 transition-colors rounded-lg"
                    >
                      <div className="flex items-center gap-3">
                        <span className="font-body text-caption text-text-secondary">
                          {isExpanded ? '\u25BE' : '\u25B8'}
                        </span>
                        {isActive && (
                          <span className="w-2 h-2 rounded-full bg-accent animate-pulse" />
                        )}
                        <span className="font-body text-body-sm text-text-primary font-medium">
                          with {counterpart}
                        </span>
                        <span className={`font-data text-caption px-1.5 py-0.5 rounded ${
                          isActive ? 'bg-accent/10 text-accent' : 'bg-text-secondary/10 text-text-secondary'
                        }`}>
                          {mtg.status}
                        </span>
                      </div>
                      <div className="flex items-center gap-3 font-data text-caption text-text-secondary">
                        <span>R{mtg.round_num}</span>
                        <span>{msgs.length > 0 ? `${msgs.length} msgs` : ''}</span>
                        <span>{new Date(mtg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                      </div>
                    </button>
                    {isExpanded && (
                      <div className="px-4 pb-3 border-t border-border/50">
                        {msgs.length === 0 ? (
                          <p className="font-body text-caption text-text-secondary py-2">
                            Loading messages...
                          </p>
                        ) : (
                          <div className="space-y-2 mt-2 max-h-80 overflow-y-auto">
                            {msgs.map((msg) => {
                              const isOurs = msg.role_id === roleId
                              return (
                                <div
                                  key={msg.id}
                                  className={`rounded-lg p-2.5 ${
                                    isOurs
                                      ? 'bg-action/5 border border-action/20 ml-8'
                                      : 'bg-base border border-border mr-8'
                                  }`}
                                >
                                  <div className="flex items-center gap-2 mb-1">
                                    <span className="font-data text-caption font-medium text-text-primary">
                                      {getRoleName(msg.role_id)}
                                    </span>
                                    <span className="font-data text-caption text-text-secondary">
                                      Turn {msg.turn_number}
                                    </span>
                                  </div>
                                  <p className="font-body text-caption text-text-primary whitespace-pre-wrap">
                                    {msg.content}
                                  </p>
                                </div>
                              )
                            })}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </Section>

        {/* Section 3: Memory Notes */}
        <Section title="Memory Notes" count={memories.length} defaultOpen={memories.length > 0}>
          {memories.length === 0 ? (
            <p className="font-body text-caption text-text-secondary">No memory notes yet.</p>
          ) : (
            <div className="space-y-1 max-h-96 overflow-y-auto">
              {memories.map((mem) => {
                const isExpanded = expandedMemories.has(mem.id)
                const preview = mem.content.length > 100
                  ? mem.content.slice(0, 100) + '...'
                  : mem.content

                return (
                  <div
                    key={mem.id}
                    className="cursor-pointer hover:bg-base/50 rounded px-2 py-1.5 transition-colors"
                    onClick={() => toggleMemory(mem.id)}
                  >
                    <div className="flex items-center gap-2">
                      <span className="font-body text-caption text-text-secondary flex-shrink-0">
                        {isExpanded ? '\u25BE' : '\u25B8'}
                      </span>
                      <span className="font-data text-caption text-accent flex-shrink-0 font-medium">
                        {mem.memory_type}
                      </span>
                      <span className="font-data text-caption text-text-secondary flex-shrink-0">
                        R{mem.round_num}
                      </span>
                      {!isExpanded && (
                        <span className="font-body text-caption text-text-primary truncate">
                          {preview}
                        </span>
                      )}
                      <span className="font-data text-caption text-text-secondary ml-auto flex-shrink-0">
                        {new Date(mem.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                    {isExpanded && (
                      <div className="ml-6 mt-2 font-body text-caption text-text-primary whitespace-pre-wrap bg-base border border-border rounded p-3">
                        {mem.content}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </Section>

        {/* Section 4: Submitted Actions */}
        <Section title="Submitted Actions" count={decisions.length} defaultOpen={decisions.length > 0}>
          {decisions.length === 0 ? (
            <p className="font-body text-caption text-text-secondary">No actions submitted yet.</p>
          ) : (
            <div className="space-y-1 max-h-96 overflow-y-auto">
              {decisions.map((dec) => {
                const isExpanded = expandedDecisions.has(dec.id)
                const statusColor =
                  dec.validation_status === 'executed' ? 'text-success' :
                  dec.validation_status === 'dispatch_failed' ? 'text-danger' :
                  dec.validation_status === 'valid' ? 'text-action' :
                  dec.validation_status === 'rejected' ? 'text-danger' :
                  'text-text-secondary'

                // Build human-readable summary of the decision
                const p = dec.action_payload || {}
                let summary = ''
                if (dec.action_type === 'set_budget')
                  summary = `social=${p.social_pct}× mil=${p.military_coins} tech=${p.tech_coins}`
                else if (dec.action_type === 'set_tariffs')
                  summary = `→ ${p.target_country} level ${p.level}`
                else if (dec.action_type === 'set_sanctions')
                  summary = `→ ${p.target_country} level ${p.level}`
                else if (dec.action_type === 'set_opec')
                  summary = `production: ${p.production}`
                else if (dec.action_type === 'public_statement')
                  summary = String(p.content || '').slice(0, 60)
                else if (dec.action_type === 'propose_transaction')
                  summary = `→ ${p.counterpart_country}`
                else if (dec.action_type === 'propose_agreement')
                  summary = `${p.agreement_type} → ${p.counterpart_country}`
                else if (dec.action_type === 'covert_operation')
                  summary = `${p.op_type} → ${p.target_country}`
                else if (['ground_attack','air_strike','naval_combat','naval_bombardment'].includes(dec.action_type))
                  summary = `target (${p.target_global_row},${p.target_global_col})`
                else if (dec.action_type === 'move_units')
                  summary = p.decision === 'no_change' ? 'no changes' : `${((p.changes as Record<string,unknown>)?.moves as unknown[] || []).length} moves`
                else
                  summary = dec.validation_notes || ''

                return (
                  <div
                    key={dec.id}
                    className="cursor-pointer hover:bg-base/50 rounded px-2 py-1.5 transition-colors"
                    onClick={() => toggleDecision(dec.id)}
                  >
                    <div className="flex items-center gap-2">
                      <span className="font-body text-caption text-text-secondary flex-shrink-0">
                        {isExpanded ? '\u25BE' : '\u25B8'}
                      </span>
                      <span className="font-data text-caption text-action font-medium flex-shrink-0">
                        {dec.action_type}
                      </span>
                      <span className="font-body text-caption text-text-primary truncate flex-1">
                        {summary}
                      </span>
                      <span className={`font-data text-caption flex-shrink-0 ${statusColor}`}>
                        {dec.validation_status}
                      </span>
                      <span className="font-data text-caption text-text-secondary flex-shrink-0 ml-auto">
                        R{dec.round_num}
                      </span>
                    </div>
                    {isExpanded && (
                      <div className="ml-6 mt-2 space-y-2">
                        {dec.rationale && (
                          <div>
                            <span className="font-data text-caption text-text-secondary">Rationale:</span>
                            <p className="font-body text-caption text-text-primary italic mt-0.5">
                              {dec.rationale}
                            </p>
                          </div>
                        )}
                        {dec.validation_notes && (
                          <div>
                            <span className="font-data text-caption text-text-secondary">Result:</span>
                            <p className="font-body text-caption text-text-primary mt-0.5">
                              {dec.validation_notes}
                            </p>
                          </div>
                        )}
                        <pre className="font-data text-caption text-text-secondary whitespace-pre-wrap bg-base border border-border rounded p-2 max-h-48 overflow-y-auto">
                          {JSON.stringify(dec.action_payload, null, 2)}
                        </pre>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </Section>

        {/* Section 5: Session Info */}
        <Section title="Session Info" defaultOpen={false}>
          {session ? (
            <div className="grid grid-cols-2 md:grid-cols-3 gap-x-8 gap-y-2 font-data text-caption">
              <div>
                <span className="text-text-secondary">Session ID</span>
                <p className="text-text-primary break-all">{session.id}</p>
              </div>
              <div>
                <span className="text-text-secondary">Role ID</span>
                <p className="text-text-primary break-all">{session.role_id}</p>
              </div>
              <div>
                <span className="text-text-secondary">Environment ID</span>
                <p className="text-text-primary break-all">{session.environment_id ?? 'N/A'}</p>
              </div>
              <div>
                <span className="text-text-secondary">Model</span>
                <p className="text-text-primary">{session.model ?? 'N/A'}</p>
              </div>
              <div>
                <span className="text-text-secondary">Status</span>
                <p className="text-text-primary">{session.status}</p>
              </div>
              <div>
                <span className="text-text-secondary">Country Code</span>
                <p className="text-text-primary">{session.country_code}</p>
              </div>
              <div>
                <span className="text-text-secondary">Input Tokens</span>
                <p className="text-text-primary">{session.total_input_tokens.toLocaleString()}</p>
              </div>
              <div>
                <span className="text-text-secondary">Output Tokens</span>
                <p className="text-text-primary">{session.total_output_tokens.toLocaleString()}</p>
              </div>
              <div>
                <span className="text-text-secondary">Cost</span>
                <p className="text-text-primary">${((session.total_output_tokens || 0) * 15 / 1000000).toFixed(4)}</p>
              </div>
              <div>
                <span className="text-text-secondary">Events Sent</span>
                <p className="text-text-primary">{session.events_sent}</p>
              </div>
              <div>
                <span className="text-text-secondary">Actions Submitted</span>
                <p className="text-text-primary">{session.actions_submitted}</p>
              </div>
              <div>
                <span className="text-text-secondary">Tool Calls</span>
                <p className="text-text-primary">{session.tool_calls}</p>
              </div>
              <div>
                <span className="text-text-secondary">Created At</span>
                <p className="text-text-primary">{new Date(session.created_at).toLocaleString()}</p>
              </div>
              <div>
                <span className="text-text-secondary">Last Active</span>
                <p className="text-text-primary">
                  {session.last_active_at ? new Date(session.last_active_at).toLocaleString() : 'N/A'}
                </p>
              </div>
            </div>
          ) : (
            <p className="font-body text-caption text-text-secondary">No session data available.</p>
          )}
        </Section>

      </main>
    </div>
  )
}
