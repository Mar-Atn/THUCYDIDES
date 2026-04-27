/**
 * AIParticipantDashboard — facilitator observability for AI agents.
 *
 * Two-line agent rows: name + status + activity + actions, country + meetings.
 * Click row → opens detail page (route TBD, currently console.log).
 *
 * Self-contained: handles own data fetching, polling (5s), and state.
 * Spec: MODULES/M5_AI_PARTICIPANT/SPEC_M5_AI_PARTICIPANT.md (D9)
 */

import { useEffect, useState, useCallback, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { supabase } from '@/lib/supabase'
import {
  getAIStatus,
  initializeAIAgents,
  shutdownAIAgents,
  freezeAgent,
  resumeAgent,
  resumeAllAgents,
  stopAllAgents,
  getAISettings,
  updateAISetting,
  getAgentLog,
  getAgentMemories,
  getSimRunRoles,
  updateRole,
  type AIStatusResponse,
  type AIAgentStatus,
  type AgentLogEntry,
  type AgentMemory,
  type SimRunRole,
} from '@/lib/queries'
import { fetchElevenLabsAgents, type ElevenLabsAgent } from '@/lib/elevenlabs-api'
import { Volume2 } from 'lucide-react'

/* -------------------------------------------------------------------------- */
/*  Constants                                                                  */
/* -------------------------------------------------------------------------- */

const POLL_INTERVAL_MS = 5000

const STATE_COLORS: Record<string, { dot: string; badge: string }> = {
  INITIALIZING: { dot: 'bg-action animate-pulse',  badge: 'bg-action/10 text-action' },
  IDLE:         { dot: 'bg-success',                badge: 'bg-success/10 text-success' },
  THINKING:     { dot: 'bg-action',                 badge: 'bg-action/10 text-action' },
  ACTING:       { dot: 'bg-warning',                badge: 'bg-warning/10 text-warning' },
  IN_MEETING:   { dot: 'bg-accent',                 badge: 'bg-accent/10 text-accent' },
  FROZEN:       { dot: 'bg-text-secondary',         badge: 'bg-text-secondary/10 text-text-secondary' },
  TERMINATED:   { dot: 'bg-danger',                 badge: 'bg-danger/10 text-danger' },
}

const DEFAULT_STYLE = { dot: 'bg-text-secondary/30', badge: 'bg-text-secondary/10 text-text-secondary' }

function stateStyle(state: string) {
  return STATE_COLORS[state] ?? DEFAULT_STYLE
}

/* -------------------------------------------------------------------------- */
/*  Activity Descriptor — fixed list of 24 labels                              */
/* -------------------------------------------------------------------------- */

interface LatestEvent {
  category: string
  summary: string
}

/** Map latest observatory event to a human-readable activity label. */
function getActivityDescriptor(latestEvent: LatestEvent | null, agentState: string): string {
  // State-based descriptors take priority when agent is not actively processing
  if (agentState === 'IDLE' && !latestEvent) return 'Ready'
  if (agentState === 'IDLE') {
    // Agent is idle — show what it LAST did, not what it's doing now
    // Only show active descriptors when ACTING
    return 'Ready'
  }
  if (agentState === 'INITIALIZING') return 'Initializing session'
  if (agentState === 'IN_MEETING') return 'In meeting'
  if (agentState === 'FROZEN') {
    if (!latestEvent) return 'Frozen'
    // Show last activity
  }
  if (agentState === 'NOT_INITIALIZED') return 'Not initialized'

  if (!latestEvent) return 'Waiting for update'

  const cat = latestEvent.category
  const sum = (latestEvent.summary || '').toLowerCase()

  // Frozen agents show "Last: {descriptor}"
  const prefix = agentState === 'FROZEN' ? 'Last: ' : ''

  if (cat === 'agent_tool_call') {
    if (sum.includes('get_my_country')) return prefix + 'Checking own status'
    if (sum.includes('get_my_forces')) return prefix + 'Reviewing forces'
    if (sum.includes('get_relationships')) return prefix + 'Checking relationships'
    if (sum.includes('get_my_artefacts')) return prefix + 'Reading intel'
    if (sum.includes('get_recent_events')) return prefix + 'Scanning events'
    if (sum.includes('get_country_info')) {
      const match = sum.match(/get_country_info\((\w+)\)/) || sum.match(/country_code.*?(\w+)/)
      return prefix + 'Looking up ' + (match?.[1] || 'country')
    }
    if (sum.includes('get_hex_info')) return prefix + 'Checking map position'
    if (sum.includes('get_pending_proposals')) return prefix + 'Reviewing proposals'
    if (sum.includes('get_action_rules')) return prefix + 'Checking action rules'
    if (sum.includes('get_organizations')) return prefix + 'Checking organizations'
    if (sum.includes('read_notes') || sum.includes('list_my_memories')) return prefix + 'Reading notes'
    if (sum.includes('write_notes') || sum.includes('write_memory')) return prefix + 'Writing notes'
    if (sum.includes('request_meeting')) return prefix + 'Requesting meeting'
    if (sum.includes('respond_to_invitation')) return prefix + 'Responding to invitation'
    if (sum.includes('submit_action') || sum.includes('commit_action')) {
      if (sum.includes('declare_attack') || sum.includes('move_units') || sum.includes('blockade') || sum.includes('naval') || sum.includes('nuclear')) return prefix + 'Submitting military action'
      if (sum.includes('set_tariff') || sum.includes('set_sanction') || sum.includes('set_budget') || sum.includes('set_opec')) return prefix + 'Submitting economic action'
      if (sum.includes('public_statement')) return prefix + 'Issuing public statement'
      if (sum.includes('covert')) return prefix + 'Launching covert operation'
      if (sum.includes('transaction') || sum.includes('agreement')) return prefix + 'Proposing transaction'
      if (sum.includes('rd_investment')) return prefix + 'Investing in R&D'
      if (sum.includes('call_org_meeting')) return prefix + 'Calling org meeting'
      return prefix + 'Submitting action'
    }
    return prefix + 'Using tool'
  }

  if (cat === 'agent_reasoning') return prefix + 'Analyzing situation'

  return prefix + 'Processing'
}

/* -------------------------------------------------------------------------- */
/*  Voice agent icon + inline selector                                         */
/* -------------------------------------------------------------------------- */

/** Shared cache so all rows don't re-fetch. */
let _agentCache: ElevenLabsAgent[] | null = null

function VoiceAgentIcon({ roleId, hasVoice, onAssigned }: {
  roleId: string
  hasVoice: boolean
  onAssigned: () => void
}) {
  const [open, setOpen] = useState(false)
  const [agents, setAgents] = useState<ElevenLabsAgent[]>(_agentCache ?? [])
  const [loading, setLoading] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  // Close on outside click
  useEffect(() => {
    if (!open) return
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [open])

  const handleOpen = async (e: React.MouseEvent) => {
    e.stopPropagation()
    setOpen(prev => !prev)
    if (!_agentCache) {
      setLoading(true)
      try {
        const data = await fetchElevenLabsAgents()
        _agentCache = data
        setAgents(data)
      } catch { /* non-critical */ }
      finally { setLoading(false) }
    }
  }

  const handleSelect = async (agentId: string | null, e: React.MouseEvent) => {
    e.stopPropagation()
    try {
      await updateRole(roleId, { elevenlabs_agent_id: agentId } as Record<string, unknown>)
      onAssigned()
    } catch { /* non-critical */ }
    setOpen(false)
  }

  return (
    <div ref={ref} className="relative flex items-center justify-center">
      <button
        onClick={handleOpen}
        className={`transition-colors ${hasVoice ? 'text-accent' : 'text-text-secondary/30 hover:text-text-secondary/60'}`}
        title={hasVoice ? 'Voice agent assigned (click to change)' : 'Assign voice agent'}
      >
        <Volume2 className="w-3.5 h-3.5" />
      </button>
      {open && (
        <div className="absolute top-6 right-0 z-50 bg-card border border-border rounded shadow-lg py-1 min-w-[180px]">
          {loading && <div className="px-3 py-1 font-body text-caption text-text-secondary">Loading...</div>}
          <button
            onClick={(e) => handleSelect(null, e)}
            className="w-full text-left px-3 py-1 font-body text-caption text-text-secondary hover:bg-base/50 transition-colors"
          >
            (none)
          </button>
          {agents.map((a) => (
            <button
              key={a.agent_id}
              onClick={(e) => handleSelect(a.agent_id, e)}
              className="w-full text-left px-3 py-1 font-body text-caption text-text-primary hover:bg-base/50 transition-colors truncate"
            >
              {a.name}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

/* -------------------------------------------------------------------------- */
/*  Main Component                                                             */
/* -------------------------------------------------------------------------- */

export function AIParticipantDashboard({ simId }: { simId: string }) {
  const navigate = useNavigate()
  const [status, setStatus] = useState<AIStatusResponse | null>(null)
  const [roles, setRoles] = useState<SimRunRole[]>([])
  const [collapsed, setCollapsed] = useState(false)
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [actionLoading, setActionLoading] = useState<string | null>(null)
  const [initializing, setInitializing] = useState(false)
  const [initDismissed, setInitDismissed] = useState(false)
  const [dbSessions, setDbSessions] = useState<Record<string, unknown>[]>([])
  const [latestActivity, setLatestActivity] = useState<Record<string, LatestEvent>>({}) // role_id → latest event
  const [activeMeetings, setActiveMeetings] = useState<Record<string, number>>({}) // role_id → active meeting count
  const [pulsesPerRound, setPulsesPerRound] = useState(8)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // Load pulses_per_round setting on mount
  useEffect(() => {
    getAISettings().then((s) => {
      const v = parseInt(s.pulses_per_round || '8', 10)
      if (!isNaN(v)) setPulsesPerRound(Math.max(0, Math.min(10, v)))
    }).catch(() => {})
  }, [])

  /* Fetch roles — poll every 5s so AI/human toggles in participant management show up */
  useEffect(() => {
    const fetchRoles = () => getSimRunRoles(simId).then(setRoles).catch(() => {})
    fetchRoles()
    const interval = setInterval(fetchRoles, 5000)
    return () => clearInterval(interval)
  }, [simId])

  /* Fetch DB sessions + latest activity — all queries in PARALLEL */
  const fetchDbData = useCallback(async () => {
    const [sessionsRes, logsRes, meetingsRes] = await Promise.allSettled([
      supabase
        .from('ai_agent_sessions')
        .select('role_id,country_code,status,agent_state,total_output_tokens,actions_submitted,tool_calls,last_active_at')
        .eq('sim_run_id', simId)
        .not('status', 'in', '("archived","terminated")'),
      supabase
        .from('observatory_events')
        .select('country_code,category,summary,created_at')
        .eq('sim_run_id', simId)
        .eq('event_type', 'ai_agent_log')
        .order('created_at', { ascending: false })
        .limit(20),
      supabase
        .from('meetings')
        .select('participant_a_role_id,participant_b_role_id')
        .eq('sim_run_id', simId)
        .eq('status', 'active'),
    ])

    // Sessions
    if (sessionsRes.status === 'fulfilled' && sessionsRes.value.data) {
      setDbSessions(sessionsRes.value.data)
      setLoading(false)  // Show data as soon as sessions arrive
    }

    // Latest activity
    if (logsRes.status === 'fulfilled' && logsRes.value.data) {
      const latest: Record<string, LatestEvent> = {}
      for (const log of logsRes.value.data) {
        const cc = log.country_code as string
        if (!latest[cc]) {
          latest[cc] = {
            category: (log.category as string) || '',
            summary: (log.summary as string) || '',
          }
        }
      }
      setLatestActivity(latest)
    }

    // Active meetings
    if (meetingsRes.status === 'fulfilled' && meetingsRes.value.data) {
      const counts: Record<string, number> = {}
      for (const m of meetingsRes.value.data) {
        const a = m.participant_a_role_id as string
        const b = m.participant_b_role_id as string
        counts[a] = (counts[a] || 0) + 1
        counts[b] = (counts[b] || 0) + 1
      }
      setActiveMeetings(counts)
    }

    setLoading(false)
  }, [simId])

  /* Realtime subscriptions for agent sessions + activity + fallback poll */
  useEffect(() => {
    fetchDbData()

    // Realtime: auto-refresh on ai_agent_sessions changes
    const sessionChannel = supabase
      .channel(`ai-sessions-${simId}`)
      .on('postgres_changes', {
        event: '*', schema: 'public', table: 'ai_agent_sessions',
        filter: `sim_run_id=eq.${simId}`,
      }, () => { fetchDbData() })
      .subscribe()

    // Realtime: auto-refresh on new observatory events (agent activity)
    const activityChannel = supabase
      .channel(`ai-activity-${simId}`)
      .on('postgres_changes', {
        event: 'INSERT', schema: 'public', table: 'observatory_events',
        filter: `sim_run_id=eq.${simId}`,
      }, () => { fetchDbData() })
      .subscribe()

    // Realtime: auto-refresh on meetings changes (status, turn_count)
    const meetingsChannel = supabase
      .channel(`ai-meetings-${simId}`)
      .on('postgres_changes', {
        event: '*', schema: 'public', table: 'meetings',
        filter: `sim_run_id=eq.${simId}`,
      }, () => { fetchDbData() })
      .subscribe()

    // Fallback poll every 15s (covers connection drops)
    const interval = setInterval(fetchDbData, 15000)

    return () => {
      supabase.removeChannel(sessionChannel)
      supabase.removeChannel(activityChannel)
      supabase.removeChannel(meetingsChannel)
      clearInterval(interval)
    }
  }, [simId, fetchDbData])

  /* Poll AI orchestrator status (backend API — may be slow on cold start) */
  const fetchStatus = useCallback(async () => {
    try {
      const data = await getAIStatus(simId)
      setStatus(data)
    } catch {
      // Orchestrator may not be active
    }
  }, [simId])

  useEffect(() => {
    fetchStatus()
    pollRef.current = setInterval(fetchStatus, POLL_INTERVAL_MS)
    return () => {
      if (pollRef.current) clearInterval(pollRef.current)
    }
  }, [fetchStatus])

  /* Role lookup helper */
  const roleMap = new Map(roles.map(r => [r.id, r]))
  const getCharName = (roleId: string) => roleMap.get(roleId)?.character_name ?? roleId.slice(0, 8)
  const getCountryCode = (agent: AIAgentStatus) => agent.country_code

  /* Freeze / Resume handlers */
  const handleResumeAll = async () => {
    setActionLoading('resume-all')
    try { await resumeAllAgents(simId); await fetchStatus() }
    catch (e) { alert(e instanceof Error ? e.message : 'Resume all failed') }
    finally { setActionLoading(null) }
  }

  const handlePulsesChange = async (val: number) => {
    const clamped = Math.max(0, Math.min(10, val))
    setPulsesPerRound(clamped)
    try {
      await updateAISetting('pulses_per_round', String(clamped))
    } catch { /* non-critical */ }
  }

  const handleStopAll = async () => {
    if (!confirm('STOP ALL AI?\n\nThis will freeze all agents and clear all pending events.\nAgents will start fresh on resume.')) return
    setActionLoading('stop-all')
    try {
      const result = await stopAllAgents(simId)
      alert(`Stopped: ${result.frozen_count} agents frozen, ${result.events_cleared} events cleared.`)
      await fetchStatus()
    }
    catch (e) { alert(e instanceof Error ? e.message : 'Stop all failed') }
    finally { setActionLoading(null) }
  }

  const handleFreezeOne = async (roleId: string) => {
    setActionLoading(`freeze-${roleId}`)
    try { await freezeAgent(simId, roleId); await fetchStatus() }
    catch (e) { alert(e instanceof Error ? e.message : 'Freeze failed') }
    finally { setActionLoading(null) }
  }

  const handleResumeOne = async (roleId: string) => {
    setActionLoading(`resume-${roleId}`)
    try { await resumeAgent(simId, roleId); await fetchStatus() }
    catch (e) { alert(e instanceof Error ? e.message : 'Resume failed') }
    finally { setActionLoading(null) }
  }

  const handleShutdown = async () => {
    if (!confirm('Shut down all AI agents? This archives all sessions.')) return
    setActionLoading('shutdown')
    try {
      await shutdownAIAgents(simId)
      setInitializing(false)
      await fetchStatus()
    } catch (e) { alert(e instanceof Error ? e.message : 'Shutdown failed') }
    finally { setActionLoading(null) }
  }

  /* Derived data */
  const aiRoles = roles.filter(r => r.is_ai_operated && r.status === 'active')
  const dbSessionMap = new Map(dbSessions.map(s => [s.role_id as string, s]))
  const activeSessions = dbSessions.filter(s => s.status !== 'archived' && s.status !== 'terminated')
  const totalActions = (status as Record<string, unknown>)?.total_actions as number ?? 0
  const totalToolCalls = (status as Record<string, unknown>)?.total_tool_calls as number ?? 0
  const agentCount = status?.total_agents ?? 0
  const isActive = agentCount > 0 || activeSessions.length > 0  // orchestrator OR DB sessions
  const noAiRoles = aiRoles.length === 0

  const handleInitialize = async () => {
    setInitializing(true)
    try {
      await initializeAIAgents(simId)
    } catch (e) {
      alert(e instanceof Error ? e.message : 'Initialization failed')
      setInitializing(false)
    }
  }

  // Auto-clear initializing when all agents appear
  if (initializing && agentCount >= aiRoles.length && aiRoles.length > 0) {
    setInitializing(false)
  }

  // Build agent status lookup from orchestrator status (when available)
  const orchAgentMap = new Map(
    (status?.agents ?? []).map((a: AIAgentStatus) => [a.role_id, a])
  )

  // Footer counters — use orchestrator status, supplement with DB meeting data
  const aiRoleIds = new Set(aiRoles.map(r => r.id))
  const aiInMeetingCount = Object.entries(activeMeetings).filter(([rid]) => aiRoleIds.has(rid)).length
  const countByState = { idle: 0, meeting: 0, frozen: 0 }
  if (status) {
    countByState.idle = status.agents_idle
    countByState.meeting = Math.max(status.agents_in_meeting, aiInMeetingCount)
    countByState.frozen = status.agents_frozen
  }

  // No AI roles at all
  if (noAiRoles && !loading) {
    return (
      <section className="bg-card border border-border rounded-lg p-5">
        <h3 className="font-heading text-h3 text-text-primary">AI Participants</h3>
        <p className="font-body text-body-sm text-text-secondary py-2">No AI-operated roles in this simulation.</p>
      </section>
    )
  }

  /* ── RENDER ─────────────────────────────────────────────────────────────── */
  return (
    <section className="bg-card border border-border rounded-lg">
      {/* ── Header ─────────────────────────────────────────────────────── */}
      <div className="px-5 py-3 border-b border-border">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h3 className="font-heading text-h3 text-text-primary">AI Participants</h3>
            <span className="font-data text-caption bg-action/10 text-action px-2 py-0.5 rounded-full">
              {isActive ? agentCount : aiRoles.length}
            </span>
            {isActive && status && (
              <span className="font-data text-caption text-text-secondary">
                ${status.total_cost_usd.toFixed(2)}
              </span>
            )}
          </div>
          <div className="flex items-center gap-3">
            {/* Pulses per round control */}
            {isActive && (
              <div className="flex items-center gap-1.5" title="Auto-pulses per round during Phase A. 0 = manual only.">
                <label className="font-body text-caption text-text-secondary">Pulses/rnd:</label>
                <input
                  type="number"
                  min={0}
                  max={10}
                  value={pulsesPerRound}
                  onChange={(e) => handlePulsesChange(parseInt(e.target.value) || 0)}
                  className="w-12 bg-base border border-border rounded px-1.5 py-0.5 font-data text-caption text-text-primary text-center focus:outline-none focus:border-action"
                />
              </div>
            )}
            {/* Controls */}
            {!isActive && !initializing && (
              <button
                onClick={handleInitialize}
                className="font-body text-caption font-medium bg-action text-white px-3 py-1.5 rounded hover:bg-action/80 transition-colors"
              >
                Initialize AI Agents
              </button>
            )}
            {initializing && (
              <span className="font-body text-caption text-action animate-pulse">
                Initializing {agentCount}/{aiRoles.length}...
              </span>
            )}
            {isActive && (
              <>
                <button
                  onClick={handleResumeAll}
                  disabled={actionLoading === 'resume-all'}
                  className="font-body text-caption font-medium bg-success/10 text-success px-3 py-1 rounded hover:bg-success/20 transition-colors disabled:opacity-40"
                >
                  {actionLoading === 'resume-all' ? '...' : 'Resume All'}
                </button>
                <button
                  onClick={handleStopAll}
                  disabled={actionLoading === 'stop-all'}
                  className="font-body text-caption font-medium bg-danger/10 text-danger px-3 py-1 rounded hover:bg-danger/20 transition-colors disabled:opacity-40"
                >
                  {actionLoading === 'stop-all' ? '...' : '⏹ Stop All'}
                </button>
                <button
                  onClick={handleShutdown}
                  disabled={actionLoading === 'shutdown'}
                  className="font-body text-caption font-medium bg-danger/10 text-danger px-3 py-1 rounded hover:bg-danger/20 transition-colors disabled:opacity-40"
                >
                  {actionLoading === 'shutdown' ? '...' : 'Shutdown'}
                </button>
              </>
            )}
            {/* Right-side stats */}
            <span className="font-data text-caption text-text-secondary ml-2">
              {isActive && status
                ? `${totalActions} actions | R${status.round_num ?? '?'}`
                : `${aiRoles.length} AI roles`}
            </span>
          </div>
        </div>
      </div>

      {/* ── Agent Rows — 2-line layout ─────────────────────────────────── */}
      <div className="divide-y divide-border/50">
        {aiRoles.map((role) => {
          // Merge data from orchestrator status (if running) + DB sessions (during init)
          const orchAgent = orchAgentMap.get(role.id)
          const dbSession = dbSessionMap.get(role.id)

          // Determine state
          let agentState = 'NOT_INITIALIZED'
          let actions = 0
          let meetings = 0
          const event = latestActivity[role.country_code] || null

          if (orchAgent) {
            agentState = orchAgent.state
            actions = orchAgent.actions_submitted ?? orchAgent.round_stats?.actions ?? 0
          } else if (dbSession) {
            // M5.8: read agent_state from DB (write-through from dispatcher)
            const dbAgentState = dbSession.agent_state as string
            if (dbAgentState && dbAgentState !== 'IDLE') {
              agentState = dbAgentState
            } else {
              const dbStatus = dbSession.status as string
              agentState = dbStatus === 'ready' ? 'IDLE' : dbStatus === 'initializing' ? 'INITIALIZING' : dbStatus.toUpperCase()
            }
            actions = (dbSession.actions_submitted as number) || 0
          }
          // Active meetings count from DB (real-time, not from orchestrator)
          meetings = activeMeetings[role.id] || 0

          // Override display state: if agent has active meetings, show IN_MEETING
          // even when dispatcher reports IDLE (agent is idle between chat messages
          // but still logically "in a meeting")
          if (meetings > 0 && (agentState === 'IDLE' || agentState === 'ACTING')) {
            agentState = 'IN_MEETING'
          }

          const style = agentState === 'NOT_INITIALIZED'
            ? DEFAULT_STYLE
            : stateStyle(agentState)

          const charName = role.character_name
          const country = role.country_code
          const activity = getActivityDescriptor(event, agentState)

          return (
            <div
              key={role.id}
              className="px-5 py-2 cursor-pointer hover:bg-base/50 transition-colors"
              onClick={() => { window.open(`/sim/${simId}/agent/${role.id}`, '_blank') }}
            >
              {/* Grid: fixed columns for alignment across rows */}
              <div className="grid items-center gap-x-3" style={{ gridTemplateColumns: '8px 120px 90px 1fr 50px 50px 18px 28px' }}>
                {/* Row 1 */}
                <span className={`w-2 h-2 rounded-full ${style.dot}`} />
                <span className="font-body text-body-sm text-text-primary font-medium truncate">
                  {charName}
                </span>
                <span className={`font-data text-caption px-1.5 py-0.5 rounded text-center ${style.badge}`}>
                  {agentState === 'NOT_INITIALIZED' ? 'waiting' : agentState}
                </span>
                <span className="font-body text-caption text-text-secondary truncate">
                  {activity}
                </span>
                <span className="font-data text-caption text-text-secondary text-right">
                  {actions} act
                </span>
                <span className="font-data text-caption text-text-secondary text-right">
                  {meetings} mtg
                </span>
                <VoiceAgentIcon
                  roleId={role.id}
                  hasVoice={!!role.elevenlabs_agent_id}
                  onAssigned={() => {
                    // Re-fetch roles to pick up the change
                    getSimRunRoles(simId).then(setRoles).catch(() => {})
                  }}
                />
                {isActive && agentState !== 'NOT_INITIALIZED' ? (
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      agentState === 'FROZEN' ? handleResumeOne(role.id) : handleFreezeOne(role.id)
                    }}
                    disabled={actionLoading === `freeze-${role.id}` || actionLoading === `resume-${role.id}`}
                    className={`font-body text-caption px-1 py-0.5 rounded transition-colors disabled:opacity-40 text-center ${
                      agentState === 'FROZEN'
                        ? 'bg-success/10 text-success hover:bg-success/20'
                        : 'bg-text-secondary/10 text-text-secondary hover:bg-text-secondary/20'
                    }`}
                    title={agentState === 'FROZEN' ? 'Resume' : 'Freeze'}
                  >
                    {agentState === 'FROZEN' ? '\u25B6' : '\u23F8'}
                  </button>
                ) : <span />}

                {/* Row 2: country below name */}
                <span />
                <span className="font-body text-caption text-text-secondary -mt-1">
                  {country}
                </span>
                <span /><span /><span /><span /><span /><span />
              </div>
            </div>
          )
        })}
      </div>

      {/* ── Footer ─────────────────────────────────────────────────────── */}
      <div className="px-5 py-2 border-t border-border">
        <div className="flex items-center gap-4 font-data text-caption text-text-secondary">
          <span>{isActive ? agentCount : aiRoles.length} agents</span>
          {isActive && (
            <>
              <span>{countByState.idle} idle</span>
              <span>{countByState.meeting} in meeting</span>
              <span>{countByState.frozen} frozen</span>
            </>
          )}
        </div>
      </div>
    </section>
  )
}

/* -------------------------------------------------------------------------- */
/*  Level 2: Agent Detail Panel (kept for future detail page)                  */
/* -------------------------------------------------------------------------- */

function AgentDetailPanel({
  simId,
  agent,
  charName,
  onFreeze,
  onResume,
}: {
  simId: string
  agent: AIAgentStatus
  charName: string
  onFreeze: () => void
  onResume: () => void
}) {
  const [logEntries, setLogEntries] = useState<AgentLogEntry[]>([])
  const [memories, setMemories] = useState<AgentMemory[]>([])
  const [logLoading, setLogLoading] = useState(true)
  const [expandedEntries, setExpandedEntries] = useState<Set<string>>(new Set())
  const [expandedMemories, setExpandedMemories] = useState<Set<string>>(new Set())
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  /* Fetch log + memories, poll every 5s */
  const fetchData = useCallback(async () => {
    try {
      const [log, mem] = await Promise.all([
        getAgentLog(simId, agent.country_code, 50),
        getAgentMemories(simId, agent.country_code),
      ])
      setLogEntries(log)
      setMemories(mem)
    } catch {
      // Non-critical — keep showing stale data
    } finally {
      setLogLoading(false)
    }
  }, [simId, agent.country_code])

  useEffect(() => {
    fetchData()
    pollRef.current = setInterval(fetchData, POLL_INTERVAL_MS)
    return () => {
      if (pollRef.current) clearInterval(pollRef.current)
    }
  }, [fetchData])

  const toggleEntry = (id: string) => {
    setExpandedEntries(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const toggleMemory = (id: string) => {
    setExpandedMemories(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const isFrozen = agent.state === 'FROZEN'
  const style = stateStyle(agent.state)

  return (
    <div className="ml-5 mr-2 mt-1 mb-3 bg-base border border-border rounded-lg p-4 space-y-4">
      {/* Header: name + controls + session info */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className={`w-2.5 h-2.5 rounded-full ${style.dot}`} />
          <span className="font-heading text-body font-semibold text-text-primary">
            {charName}
          </span>
          <span className="font-body text-caption text-text-secondary">
            ({agent.country_code})
          </span>
          <span className={`font-data text-caption px-1.5 py-0.5 rounded ${style.badge}`}>
            {agent.state}
          </span>
        </div>
        <div className="flex gap-2">
          <button
            onClick={isFrozen ? onResume : onFreeze}
            className={`font-body text-caption font-medium px-3 py-1 rounded transition-colors ${
              isFrozen
                ? 'bg-success/10 text-success hover:bg-success/20'
                : 'bg-text-secondary/10 text-text-secondary hover:bg-text-secondary/20'
            }`}
          >
            {isFrozen ? 'Resume' : 'Freeze'}
          </button>
        </div>
      </div>

      {/* Session info row */}
      <div className="flex flex-wrap gap-4 font-data text-caption text-text-secondary">
        <span>Session: {agent.session_id.slice(0, 12)}...</span>
        <span>Model: {agent.cost.model}</span>
        <span>Tokens: {agent.cost.output_tokens.toLocaleString()} out</span>
        <span>Cost: ${agent.cost.total_cost_usd.toFixed(4)}</span>
        <span>Events: {agent.cost.events_sent}</span>
      </div>

      {/* Activity Log */}
      <div>
        <h4 className="font-heading text-body-sm font-semibold text-text-primary mb-2">
          Activity Log
        </h4>
        {logLoading ? (
          <p className="font-body text-caption text-text-secondary">Loading log...</p>
        ) : logEntries.length === 0 ? (
          <p className="font-body text-caption text-text-secondary">No activity yet</p>
        ) : (
          <div className="space-y-1 max-h-64 overflow-y-auto">
            {logEntries.map((entry) => {
              const isExpanded = expandedEntries.has(entry.id)
              const time = new Date(entry.created_at).toLocaleTimeString([], {
                hour: '2-digit',
                minute: '2-digit',
              })
              const payload = entry.payload ?? {}
              const logType = (payload.log_type as string) ?? entry.category ?? 'event'
              const detail = (payload.detail as string) ?? (payload.rationale as string) ?? ''

              return (
                <div
                  key={entry.id}
                  className="cursor-pointer hover:bg-card/50 rounded px-2 py-1 transition-colors"
                  onClick={() => toggleEntry(entry.id)}
                >
                  <div className="flex items-center gap-2">
                    <span className="font-body text-caption text-text-secondary flex-shrink-0">
                      {isExpanded ? '\u25BE' : '\u25B8'}
                    </span>
                    <span className="font-data text-caption text-text-secondary flex-shrink-0">
                      {time}
                    </span>
                    <span className={`font-data text-caption font-medium ${logTypeColor(logType)}`}>
                      {logType}
                    </span>
                    <span className="font-body text-caption text-text-primary truncate">
                      {entry.summary}
                    </span>
                  </div>
                  {isExpanded && detail && (
                    <div className="ml-6 mt-1 font-body text-caption text-text-secondary italic whitespace-pre-wrap">
                      {detail}
                    </div>
                  )}
                  {isExpanded && !detail && payload && Object.keys(payload).length > 0 && (
                    <div className="ml-6 mt-1 font-data text-caption text-text-secondary whitespace-pre-wrap">
                      {JSON.stringify(payload, null, 2)}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* Memory Notes */}
      {memories.length > 0 && (
        <div>
          <h4 className="font-heading text-body-sm font-semibold text-text-primary mb-2">
            Memory Notes
          </h4>
          <div className="space-y-1 max-h-40 overflow-y-auto">
            {memories.map((mem) => {
              const isExpanded = expandedMemories.has(mem.id)
              const preview = mem.content.length > 80
                ? mem.content.slice(0, 80) + '...'
                : mem.content

              return (
                <div
                  key={mem.id}
                  className="cursor-pointer hover:bg-card/50 rounded px-2 py-1 transition-colors"
                  onClick={() => toggleMemory(mem.id)}
                >
                  <div className="flex items-center gap-2">
                    <span className="font-body text-caption text-text-secondary flex-shrink-0">
                      {isExpanded ? '\u25BE' : '\u25B8'}
                    </span>
                    <span className="font-data text-caption text-accent flex-shrink-0">
                      {mem.memory_type}
                    </span>
                    <span className="font-data text-caption text-text-secondary flex-shrink-0">
                      (R{mem.round_num})
                    </span>
                    {!isExpanded && (
                      <span className="font-body text-caption text-text-primary truncate">
                        {preview}
                      </span>
                    )}
                  </div>
                  {isExpanded && (
                    <div className="ml-6 mt-1 font-body text-caption text-text-primary whitespace-pre-wrap">
                      {mem.content}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}

/* -------------------------------------------------------------------------- */
/*  Helpers                                                                    */
/* -------------------------------------------------------------------------- */

/** Color for log entry type labels. */
function logTypeColor(logType: string): string {
  switch (logType.toLowerCase()) {
    case 'action':
      return 'text-success'
    case 'tool':
    case 'tool_call':
      return 'text-action'
    case 'reasoning':
    case 'thought':
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
