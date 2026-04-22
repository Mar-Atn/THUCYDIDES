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
  shutdownAIAgents,
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

  /* Poll DB directly for agent sessions + latest activity (always — survives backend restart) */
  useEffect(() => {
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
  }, [simId])

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
  const totalActions = status?.agents.reduce((s, a) => s + a.round_stats.actions, 0) ?? 0
  const totalToolCalls = status?.agents.reduce((s, a) => s + a.round_stats.tool_calls, 0) ?? 0
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

  // No AI roles at all
  if (noAiRoles && !loading) {
    return (
      <section className="bg-card border border-border rounded-lg p-5">
        <h3 className="font-heading text-h3 text-text-primary">AI Participants</h3>
        <p className="font-body text-body-sm text-text-secondary py-2">No AI-operated roles in this simulation.</p>
      </section>
    )
  }

  /* ── ONE CONSISTENT LAYOUT — always shows the agent table ────────────── */
  return (
    <section className="bg-card border border-border rounded-lg">
      {/* ── Header ─────────────────────────────────────────────────────── */}
      <div
        className="flex items-center justify-between px-5 py-3 cursor-pointer hover:bg-base/50 transition-colors"
        onClick={() => setCollapsed(!collapsed)}
      >
        <div className="flex items-center gap-2">
          {initializing && (
            <div className="w-3.5 h-3.5 border-2 border-action border-t-transparent rounded-full animate-spin" />
          )}
          <h3 className="font-heading text-h3 text-text-primary">AI Participants</h3>
          <span className="font-data text-caption bg-action/10 text-action px-2 py-0.5 rounded-full">
            {isActive ? agentCount : aiRoles.length}
          </span>
          {isActive && (
            <span className="font-data text-caption text-text-secondary">
              ${status!.total_cost_usd.toFixed(2)}
            </span>
          )}
        </div>
        <span className="font-body text-caption text-text-secondary">
          {collapsed ? '\u25BC' : '\u25B2'}
        </span>
      </div>

      {!collapsed && (
        <div className="px-5 pb-5">
          {/* ── Controls ──────────────────────────────────────────── */}
          <div className="flex items-center justify-between mb-3">
            <div className="flex gap-2">
              {!isActive && !initializing && (
                <button
                  onClick={(e) => { e.stopPropagation(); handleInitialize() }}
                  className="font-body text-caption font-medium bg-action text-white px-3 py-1.5 rounded hover:bg-action/80 transition-colors"
                >
                  Initialize AI Agents
                </button>
              )}
              {isActive && (
                <>
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
                  <button
                    onClick={(e) => { e.stopPropagation(); handleShutdown() }}
                    disabled={actionLoading === 'shutdown'}
                    className="font-body text-caption font-medium bg-danger/10 text-danger px-3 py-1 rounded hover:bg-danger/20 transition-colors disabled:opacity-40"
                  >
                    {actionLoading === 'shutdown' ? '...' : 'Shutdown'}
                  </button>
                </>
              )}
              {initializing && (
                <span className="font-body text-caption text-action animate-pulse">
                  Initializing {agentCount}/{aiRoles.length}...
                </span>
              )}
            </div>
            <div className="font-data text-caption text-text-secondary">
              {isActive
                ? `${totalActions} actions | ${totalToolCalls} tool calls | R${status!.round_num} P${status!.pulse_num}`
                : `${aiRoles.length} AI roles`}
            </div>
          </div>

          {/* ── Agent Rows — ALWAYS shows all AI roles ─────────────── */}
          <div className="space-y-1">
            {aiRoles.map((role) => {
              // Merge data from orchestrator status (if running) + DB sessions (during init)
              const orchAgent = orchAgentMap.get(role.id)
              const dbSession = dbSessionMap.get(role.id)

              // Determine state
              let agentState = 'NOT_INITIALIZED'
              let actions = 0
              let costUsd = 0
              let activity = latestActivity[role.country_code] || ''

              if (orchAgent) {
                agentState = orchAgent.state
                actions = orchAgent.round_stats.actions
                costUsd = orchAgent.cost.total_cost_usd
              } else if (dbSession) {
                const dbStatus = dbSession.status as string
                agentState = dbStatus === 'ready' ? 'IDLE' : dbStatus === 'initializing' ? 'INITIALIZING' : dbStatus.toUpperCase()
                actions = (dbSession.actions_submitted as number) || 0
                costUsd = ((dbSession.total_output_tokens as number) || 0) * 15 / 1000000
              }

              const style = agentState === 'NOT_INITIALIZED'
                ? { dot: 'bg-text-secondary/30', text: 'text-text-secondary/50', bg: 'bg-base' }
                : agentState === 'INITIALIZING'
                ? { dot: 'bg-action animate-pulse', text: 'text-action', bg: 'bg-action/5' }
                : stateStyle(agentState)

              const isSelected = selectedAgent === role.id
              const charName = role.character_name
              const country = role.country_code

              return (
                <div key={role.id}>
                  {/* Row */}
                  <div
                    className={`flex items-center justify-between px-3 py-2 rounded cursor-pointer transition-colors ${
                      isSelected ? 'bg-base' : 'hover:bg-base/50'
                    }`}
                    onClick={() => setSelectedAgent(isSelected ? null : role.id)}
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
                        {agentState === 'NOT_INITIALIZED' ? 'waiting' : agentState === 'INITIALIZING' ? 'starting...' : agentState}
                      </span>
                      {/* Latest activity (shown during init or when not expanded) */}
                      {activity && !isSelected && (
                        <span className="font-body text-caption text-text-secondary/60 truncate max-w-[200px] hidden lg:inline">
                          {activity}
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-3 flex-shrink-0">
                      <span className="font-data text-caption text-text-secondary">
                        {actions} act
                      </span>
                      <span className="font-data text-caption text-text-secondary">
                        ${costUsd.toFixed(2)}
                      </span>
                      {/* Per-agent freeze/resume (only when active) */}
                      {isActive && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            agentState === 'FROZEN' ? handleResumeOne(role.id) : handleFreezeOne(role.id)
                          }}
                          disabled={actionLoading === `freeze-${role.id}` || actionLoading === `resume-${role.id}`}
                          className={`font-body text-caption px-2 py-0.5 rounded transition-colors disabled:opacity-40 ${
                            agentState === 'FROZEN'
                              ? 'bg-success/10 text-success hover:bg-success/20'
                              : 'bg-text-secondary/10 text-text-secondary hover:bg-text-secondary/20'
                          }`}
                          title={agentState === 'FROZEN' ? 'Resume' : 'Freeze'}
                        >
                          {agentState === 'FROZEN' ? '\u25B6' : '\u23F8'}
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Level 2: Detail View */}
                  {isSelected && orchAgent && (
                    <AgentDetailPanel
                      simId={simId}
                      agent={orchAgent}
                      charName={charName}
                      onFreeze={() => handleFreezeOne(role.id)}
                      onResume={() => handleResumeOne(role.id)}
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
