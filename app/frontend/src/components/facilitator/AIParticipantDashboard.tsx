/**
 * AIParticipantDashboard — facilitator observability for AI agents.
 *
 * Level 1: Overview panel — all agents at a glance with freeze/resume controls.
 * Level 2: Agent detail view — expandable activity log, memory notes, session info.
 *
 * Self-contained: handles own data fetching, polling (5s), and state.
 * Spec: MODULES/M5_AI_PARTICIPANT/SPEC_M5_AI_PARTICIPANT.md (D9)
 */

import { useEffect, useState, useCallback, useRef } from 'react'
import { supabase } from '@/lib/supabase'
import {
  getAIStatus,
  initializeAIAgents,
  freezeAgent,
  resumeAgent,
  freezeAllAgents,
  resumeAllAgents,
  getAgentLog,
  getAgentMemories,
  getSimRunRoles,
  type AIStatusResponse,
  type AIAgentStatus,
  type AgentLogEntry,
  type AgentMemory,
  type SimRunRole,
} from '@/lib/queries'

/* -------------------------------------------------------------------------- */
/*  Constants                                                                  */
/* -------------------------------------------------------------------------- */

const POLL_INTERVAL_MS = 5000

const STATE_COLORS: Record<string, { dot: string; text: string; bg: string }> = {
  IDLE:        { dot: 'bg-success',        text: 'text-success',        bg: 'bg-success/10' },
  ACTING:      { dot: 'bg-action',         text: 'text-action',         bg: 'bg-action/10' },
  IN_MEETING:  { dot: 'bg-accent',         text: 'text-accent',         bg: 'bg-accent/10' },
  FROZEN:      { dot: 'bg-text-secondary', text: 'text-text-secondary', bg: 'bg-text-secondary/10' },
  TERMINATED:  { dot: 'bg-danger',         text: 'text-danger',         bg: 'bg-danger/10' },
}

function stateStyle(state: string) {
  return STATE_COLORS[state] ?? STATE_COLORS.TERMINATED
}

/* -------------------------------------------------------------------------- */
/*  Main Component                                                             */
/* -------------------------------------------------------------------------- */

export function AIParticipantDashboard({ simId }: { simId: string }) {
  const [status, setStatus] = useState<AIStatusResponse | null>(null)
  const [roles, setRoles] = useState<SimRunRole[]>([])
  const [collapsed, setCollapsed] = useState(false)
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState<string | null>(null)
  const [initializing, setInitializing] = useState(false)
  const [initDismissed, setInitDismissed] = useState(false)
  const [dbSessions, setDbSessions] = useState<Record<string, unknown>[]>([])
  const [latestActivity, setLatestActivity] = useState<Record<string, string>>({}) // role_id → latest summary
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  /* Fetch roles once for character_name lookup */
  useEffect(() => {
    getSimRunRoles(simId).then(setRoles).catch(() => {})
  }, [simId])

  /* Poll DB directly for agent sessions + latest activity (works during init) */
  useEffect(() => {
    if (!initializing && status && status.total_agents > 0) return // orchestrator status is available, no need
    const poll = async () => {
      try {
        const { data: sessions } = await supabase
          .from('ai_agent_sessions')
          .select('role_id,country_code,status,total_output_tokens,actions_submitted,tool_calls,last_active_at')
          .eq('sim_run_id', simId)
        if (sessions) setDbSessions(sessions)

        // Latest activity per agent from observatory
        const { data: logs } = await supabase
          .from('observatory_events')
          .select('country_code,summary,created_at')
          .eq('sim_run_id', simId)
          .eq('event_type', 'ai_agent_log')
          .order('created_at', { ascending: false })
          .limit(20)
        if (logs) {
          const latest: Record<string, string> = {}
          for (const log of logs) {
            const cc = log.country_code as string
            if (!latest[cc]) {
              latest[cc] = (log.summary as string || '').slice(0, 80)
            }
          }
          setLatestActivity(latest)
        }
      } catch { /* ignore */ }
    }
    poll()
    const interval = setInterval(poll, 3000) // 3s during init for responsiveness
    return () => clearInterval(interval)
  }, [simId, initializing, status?.total_agents])

  /* Poll AI status every 5 seconds */
  const fetchStatus = useCallback(async () => {
    try {
      const data = await getAIStatus(simId)
      setStatus(data)
    } catch {
      // Orchestrator may not be active — that's fine
    } finally {
      setLoading(false)
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
  const handleFreezeAll = async () => {
    setActionLoading('freeze-all')
    try { await freezeAllAgents(simId); await fetchStatus() }
    catch (e) { alert(e instanceof Error ? e.message : 'Freeze all failed') }
    finally { setActionLoading(null) }
  }

  const handleResumeAll = async () => {
    setActionLoading('resume-all')
    try { await resumeAllAgents(simId); await fetchStatus() }
    catch (e) { alert(e instanceof Error ? e.message : 'Resume all failed') }
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

  /* Derived totals */
  const totalActions = status?.agents.reduce((s, a) => s + a.round_stats.actions, 0) ?? 0
  const totalToolCalls = status?.agents.reduce((s, a) => s + a.round_stats.tool_calls, 0) ?? 0
  const agentCount = status?.total_agents ?? 0

  /* Empty / loading states */
  if (loading) {
    return (
      <section className="bg-card border border-border rounded-lg p-5">
        <h3 className="font-heading text-h3 text-text-primary">AI Participants</h3>
        <p className="font-body text-body-sm text-text-secondary py-2">Loading...</p>
      </section>
    )
  }

  /* AI roles that need initialization */
  const aiRoles = roles.filter(r => r.is_ai_operated && r.status !== 'inactive')

  const handleInitialize = async () => {
    setInitializing(true)
    try {
      await initializeAIAgents(simId)
      // Don't reset initializing — keep showing progress until agents appear in status poll
    } catch (e) {
      alert(e instanceof Error ? e.message : 'Initialization failed')
      setInitializing(false)
    }
  }

  // Auto-clear initializing state when agents appear
  if (initializing && status && status.total_agents > 0) {
    setInitializing(false)
  }

  if (initializing) {
    const dbSessionMap = new Map(dbSessions.map(s => [s.role_id as string, s]))
    const onlineCount = dbSessions.filter(s => s.status !== 'initializing').length

    return (
      <section className="bg-card border border-action/30 rounded-lg p-5">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-4 h-4 border-2 border-action border-t-transparent rounded-full animate-spin" />
          <h3 className="font-heading text-h3 text-text-primary">
            Initializing AI Participants ({onlineCount}/{aiRoles.length})
          </h3>
        </div>

        <div className="space-y-1">
          {aiRoles.map(role => {
            const session = dbSessionMap.get(role.id)
            const sessionStatus = (session?.status as string) || 'waiting'
            const activity = latestActivity[role.country_code] || ''
            const isOnline = session && sessionStatus !== 'initializing'
            const isCreating = session && sessionStatus === 'initializing'

            return (
              <div key={role.id} className="flex items-center gap-2 py-1.5 px-2 rounded bg-base">
                {/* Status dot */}
                <div className={`w-2 h-2 rounded-full shrink-0 ${
                  isOnline ? 'bg-success' : isCreating ? 'bg-action animate-pulse' : 'bg-text-secondary/30'
                }`} />

                {/* Name + country */}
                <span className="font-body text-body-sm text-text-primary w-32 truncate">
                  {role.character_name}
                </span>
                <span className="font-body text-caption text-text-secondary uppercase w-20 truncate">
                  {role.country_code}
                </span>

                {/* Status */}
                <span className={`font-body text-caption w-20 ${
                  isOnline ? 'text-success' : isCreating ? 'text-action' : 'text-text-secondary/50'
                }`}>
                  {isOnline ? 'ready' : isCreating ? 'creating...' : 'waiting'}
                </span>

                {/* Latest activity */}
                <span className="font-body text-caption text-text-secondary/70 flex-1 truncate">
                  {activity || (isCreating ? 'Setting up session...' : '')}
                </span>
              </div>
            )
          })}
        </div>

        <p className="font-body text-caption text-text-secondary mt-3">
          Agents initialize in parallel. Each explores the game state on first contact.
        </p>
      </section>
    )
  }

  if (!status || status.total_agents === 0) {
    // Show initialization prompt if there are AI roles
    if (aiRoles.length > 0 && !initDismissed) {
      return (
        <section className="bg-card border border-action/30 rounded-lg p-5">
          <h3 className="font-heading text-h3 text-text-primary mb-2">AI Participants</h3>
          <p className="font-body text-body-sm text-text-primary mb-1">
            This simulation has <strong>{aiRoles.length} AI-operated role{aiRoles.length !== 1 ? 's' : ''}</strong>:
          </p>
          <div className="font-body text-caption text-text-secondary mb-3 flex flex-wrap gap-1">
            {aiRoles.map(r => (
              <span key={r.id} className="bg-action/10 text-action px-2 py-0.5 rounded">
                {r.character_name} ({r.country_code})
              </span>
            ))}
          </div>
          <p className="font-body text-body-sm text-text-secondary mb-3">
            Initialize them now? This creates AI agent sessions and may take 1-2 minutes.
          </p>
          <div className="flex gap-2">
            <button
              onClick={handleInitialize}
              disabled={initializing}
              className="font-body text-caption font-medium bg-action text-white px-4 py-2 rounded hover:bg-action/80 disabled:opacity-50 transition-colors"
            >
              Yes, Initialize AI
            </button>
            <button
              onClick={() => setInitDismissed(true)}
              className="font-body text-caption text-text-secondary px-4 py-2 rounded border border-border hover:bg-base transition-colors"
            >
              Later
            </button>
          </div>
          {initializing && (
            <p className="font-body text-caption text-action mt-2 animate-pulse">
              Creating AI sessions... This may take a minute.
            </p>
          )}
        </section>
      )
    }

    return (
      <section className="bg-card border border-border rounded-lg p-5">
        <h3 className="font-heading text-h3 text-text-primary">AI Participants</h3>
        <p className="font-body text-body-sm text-text-secondary py-2">
          {aiRoles.length > 0
            ? 'AI agents not yet initialized.'
            : 'No AI-operated roles in this simulation.'}
        </p>
        {aiRoles.length > 0 && (
          <button
            onClick={handleInitialize}
            disabled={initializing}
            className="font-body text-caption font-medium bg-action/10 text-action px-3 py-1 rounded hover:bg-action/20 disabled:opacity-50 transition-colors mt-1"
          >
            {initializing ? 'Initializing...' : 'Initialize AI Agents'}
          </button>
        )}
      </section>
    )
  }

  return (
    <section className="bg-card border border-border rounded-lg">
      {/* ── Collapsible Header ──────────────────────────────────────── */}
      <div
        className="flex items-center justify-between px-5 py-3 cursor-pointer hover:bg-base/50 transition-colors"
        onClick={() => setCollapsed(!collapsed)}
      >
        <div className="flex items-center gap-2">
          <h3 className="font-heading text-h3 text-text-primary">AI Participants</h3>
          <span className="font-data text-caption bg-action/10 text-action px-2 py-0.5 rounded-full">
            {agentCount}
          </span>
          <span className="font-data text-caption text-text-secondary">
            ${status.total_cost_usd.toFixed(2)}
          </span>
        </div>
        <span className="font-body text-caption text-text-secondary">
          {collapsed ? '\u25BC' : '\u25B2'}
        </span>
      </div>

      {!collapsed && (
        <div className="px-5 pb-5">
          {/* ── Global Controls ──────────────────────────────────── */}
          <div className="flex items-center justify-between mb-3">
            <div className="flex gap-2">
              <button
                onClick={(e) => { e.stopPropagation(); handleFreezeAll() }}
                disabled={actionLoading === 'freeze-all'}
                className="font-body text-caption font-medium bg-text-secondary/10 text-text-secondary px-3 py-1 rounded hover:bg-text-secondary/20 transition-colors disabled:opacity-40"
              >
                {actionLoading === 'freeze-all' ? '...' : 'Freeze All'}
              </button>
              <button
                onClick={(e) => { e.stopPropagation(); handleResumeAll() }}
                disabled={actionLoading === 'resume-all'}
                className="font-body text-caption font-medium bg-success/10 text-success px-3 py-1 rounded hover:bg-success/20 transition-colors disabled:opacity-40"
              >
                {actionLoading === 'resume-all' ? '...' : 'Resume All'}
              </button>
            </div>
            <div className="font-data text-caption text-text-secondary">
              {totalActions} actions | {totalToolCalls} tool calls | R{status.round_num} P{status.pulse_num}
            </div>
          </div>

          {/* ── Agent Rows ───────────────────────────────────────── */}
          <div className="space-y-1">
            {status.agents.map((agent) => {
              const style = stateStyle(agent.state)
              const isSelected = selectedAgent === agent.role_id
              const isFrozen = agent.state === 'FROZEN'
              const charName = getCharName(agent.role_id)
              const country = getCountryCode(agent)

              return (
                <div key={agent.role_id}>
                  {/* Row */}
                  <div
                    className={`flex items-center justify-between px-3 py-2 rounded cursor-pointer transition-colors ${
                      isSelected ? 'bg-base' : 'hover:bg-base/50'
                    }`}
                    onClick={() => setSelectedAgent(isSelected ? null : agent.role_id)}
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      {/* Status dot */}
                      <span className={`w-2 h-2 rounded-full flex-shrink-0 ${style.dot}`} />
                      {/* Name + Country */}
                      <span className="font-body text-body-sm text-text-primary truncate">
                        {charName}
                      </span>
                      <span className="font-body text-caption text-text-secondary">
                        ({country})
                      </span>
                      {/* State badge */}
                      <span className={`font-data text-caption px-1.5 py-0.5 rounded ${style.bg} ${style.text}`}>
                        {agent.state}
                      </span>
                    </div>
                    <div className="flex items-center gap-3 flex-shrink-0">
                      <span className="font-data text-caption text-text-secondary">
                        {agent.round_stats.actions} act
                      </span>
                      <span className="font-data text-caption text-text-secondary">
                        ${agent.cost.total_cost_usd.toFixed(2)}
                      </span>
                      {/* Per-agent freeze/resume */}
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          isFrozen ? handleResumeOne(agent.role_id) : handleFreezeOne(agent.role_id)
                        }}
                        disabled={actionLoading === `freeze-${agent.role_id}` || actionLoading === `resume-${agent.role_id}`}
                        className={`font-body text-caption px-2 py-0.5 rounded transition-colors disabled:opacity-40 ${
                          isFrozen
                            ? 'bg-success/10 text-success hover:bg-success/20'
                            : 'bg-text-secondary/10 text-text-secondary hover:bg-text-secondary/20'
                        }`}
                        title={isFrozen ? 'Resume' : 'Freeze'}
                      >
                        {isFrozen ? '\u25B6' : '\u23F8'}
                      </button>
                    </div>
                  </div>

                  {/* Level 2: Detail View */}
                  {isSelected && (
                    <AgentDetailPanel
                      simId={simId}
                      agent={agent}
                      charName={charName}
                      onFreeze={() => handleFreezeOne(agent.role_id)}
                      onResume={() => handleResumeOne(agent.role_id)}
                    />
                  )}
                </div>
              )
            })}
          </div>
        </div>
      )}
    </section>
  )
}

/* -------------------------------------------------------------------------- */
/*  Level 2: Agent Detail Panel                                                */
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
          <span className={`font-data text-caption px-1.5 py-0.5 rounded ${style.bg} ${style.text}`}>
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
