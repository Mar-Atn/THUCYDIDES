/**
 * Facilitator Dashboard — the moderator's cockpit during a live simulation.
 * Route: /sim/:id/live
 *
 * Sections: Top bar (fixed), Pending Actions, SIM Events Feed,
 * AI Participants, Participants, Public Screen, Map, Explore, Special Moments.
 */

import { useEffect, useState, useCallback, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Header } from '@/components/Header'
import {
  getSimRunRoles,
  simAction,
  submitAction,
  getAllUsers,
  assignUserToRole,
  toggleRoleAI,
  type SimRun,
  type SimRunRole,
  type UserRecord,
} from '@/lib/queries'
import { supabase } from '@/lib/supabase'
import { useRealtimeRow, useRealtimeTable } from '@/hooks/useRealtimeTable'
import { requestQueue } from '@/lib/requestQueue'
import { AIParticipantDashboard } from '@/components/facilitator/AIParticipantDashboard'

/* -------------------------------------------------------------------------- */
/*  Types                                                                     */
/* -------------------------------------------------------------------------- */

interface SimState {
  status: string
  current_round: number
  current_phase: string
  phase_started_at: string | null
  phase_duration_seconds: number
  mode: 'manual' | 'automatic'
  paused: boolean
  pending_actions: PendingAction[]
}

interface PendingAction {
  id: string
  sim_run_id: string
  round_num: number
  action_type: string
  role_id: string
  country_code: string
  target_info: string
  payload: Record<string, unknown>
  status: string
  submitted_at: string
}

interface ObservatoryEvent {
  id: string
  sim_run_id: string
  round_num: number
  event_type: string
  country_code: string | null
  summary: string
  payload: Record<string, unknown> | null
  phase: string | null
  category: string | null
  role_name: string | null
  created_at: string
}

interface KeyEvent {
  round: number
  type: string
  name?: string
  subtype?: string
  description?: string
  country?: string
  country_code?: string
  organization?: string
  nominations_round?: number
  participants?: Record<string, unknown>[]
}

/* -------------------------------------------------------------------------- */
/*  Phase badge helpers                                                       */
/* -------------------------------------------------------------------------- */

function phaseBadgeClass(phase: string, paused: boolean): string {
  if (paused) return 'bg-text-secondary/20 text-text-secondary'
  switch (phase) {
    case 'phase_a':
      return 'bg-success/20 text-success'
    case 'phase_b':
      return 'bg-warning/20 text-warning'
    case 'inter_round':
      return 'bg-action/20 text-action'
    case 'pre':
      return 'bg-text-secondary/20 text-text-secondary'
    case 'post':
      return 'bg-accent/20 text-accent'
    default:
      return 'bg-text-secondary/20 text-text-secondary'
  }
}

function phaseLabel(phase: string, paused: boolean): string {
  if (paused) return 'Paused'
  switch (phase) {
    case 'phase_a':
      return 'Phase A'
    case 'phase_b':
      return 'Phase B'
    case 'inter_round':
      return 'Inter-Round'
    case 'pre':
      return 'Pre-Start'
    case 'post':
      return 'Post-Sim'
    default:
      return phase
  }
}

function categoryColor(category: string): string {
  switch (category?.toLowerCase()) {
    case 'military':
    case 'mil':
      return 'text-danger'
    case 'economic':
    case 'econ':
      return 'text-accent'
    case 'diplomatic':
    case 'dipl':
      return 'text-action'
    case 'covert':
    case 'cov':
      return 'text-text-secondary'
    case 'political':
    case 'pol':
      return 'text-warning'
    default:
      return 'text-text-secondary'
  }
}

function categoryBadgeClass(category: string): string {
  switch (category?.toLowerCase()) {
    case 'military':
    case 'mil':
      return 'bg-danger/10 text-danger'
    case 'economic':
    case 'econ':
      return 'bg-accent/10 text-accent'
    case 'diplomatic':
    case 'dipl':
      return 'bg-action/10 text-action'
    case 'covert':
    case 'cov':
      return 'bg-text-secondary/10 text-text-secondary'
    case 'political':
    case 'pol':
      return 'bg-warning/10 text-warning'
    default:
      return 'bg-text-secondary/10 text-text-secondary'
  }
}

/** AI event types — agent thinking/tool calls, not real game actions */
const AI_EVENT_TYPES = new Set([
  'ai_agent_log', 'agent_started', 'agent_committed', 'agent_no_commit',
])

function EventsFeedCard({ events }: { events: ObservatoryEvent[] }) {
  const [tab, setTab] = useState<'sim' | 'ai'>('sim')

  const simEvents = events.filter((e) => !AI_EVENT_TYPES.has(e.event_type))
  const aiEvents = events.filter((e) => AI_EVENT_TYPES.has(e.event_type))
  const displayed = tab === 'sim' ? simEvents : aiEvents

  return (
    <div className="bg-card border border-border rounded-lg p-5">
      {/* Tab bar */}
      <div className="flex items-center gap-1 mb-3">
        <button
          onClick={() => setTab('sim')}
          className={`font-heading text-h3 px-3 py-1 rounded transition-colors ${
            tab === 'sim'
              ? 'text-text-primary bg-base'
              : 'text-text-secondary hover:text-text-primary'
          }`}
        >
          SIM Events
          {simEvents.length > 0 && (
            <span className="ml-2 font-data text-caption bg-action/10 text-action px-2 py-0.5 rounded-full">
              {simEvents.length}
            </span>
          )}
        </button>
        <button
          onClick={() => setTab('ai')}
          className={`font-heading text-h3 px-3 py-1 rounded transition-colors ${
            tab === 'ai'
              ? 'text-text-primary bg-base'
              : 'text-text-secondary hover:text-text-primary'
          }`}
        >
          AI Reflections
          {aiEvents.length > 0 && (
            <span className="ml-2 font-data text-caption bg-accent/10 text-accent px-2 py-0.5 rounded-full">
              {aiEvents.length}
            </span>
          )}
        </button>
      </div>

      {/* Event list */}
      {displayed.length === 0 ? (
        <div className="min-h-[30vh] flex items-center justify-center">
          <p className="font-body text-body-sm text-text-secondary">
            {tab === 'sim' ? 'No game events yet' : 'No AI activity yet'}
          </p>
        </div>
      ) : (
        <div className="space-y-1 min-h-[30vh] max-h-[30vh] overflow-y-auto">
          {displayed.map((evt) => (
            <div
              key={evt.id}
              className="flex items-start gap-3 px-3 py-2 rounded hover:bg-base transition-colors"
            >
              <span className="font-data text-caption text-text-secondary w-14 shrink-0">
                {new Date(evt.created_at).toLocaleTimeString([], {
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </span>
              <span className="font-body text-body-sm text-text-primary font-medium w-24 shrink-0">
                {evt.role_name ?? evt.country_code ?? '---'}
              </span>
              <span className="font-body text-body-sm text-text-primary flex-1">
                {evt.summary}
              </span>
              <span
                className={`font-body text-caption font-medium px-2 py-0.5 rounded shrink-0 ${categoryBadgeClass(evt.category ?? '')}`}
              >
                {evt.category?.toUpperCase().slice(0, 4) ?? evt.event_type?.slice(0, 4).toUpperCase() ?? '---'}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function positionBadgeClass(position: string): string {
  switch (position) {
    case 'head_of_state':
      return 'bg-warning/15 text-warning'
    case 'military': case 'military_chief':
      return 'bg-danger/15 text-danger'
    case 'economy': case 'economy_officer':
      return 'bg-accent/15 text-accent'
    case 'diplomat':
      return 'bg-action/15 text-action'
    case 'security':
      return 'bg-text-secondary/15 text-text-secondary'
    case 'opposition':
      return 'bg-text-secondary/10 text-text-secondary'
    default:
      return 'bg-base text-text-secondary'
  }
}

function positionLabel(position: string): string {
  switch (position) {
    case 'head_of_state': return 'HoS'
    case 'military': case 'military_chief': return 'Mil'
    case 'economy': case 'economy_officer': return 'Econ'
    case 'diplomat': return 'Dipl'
    case 'security': return 'Sec'
    case 'opposition': return 'Opp'
    default: return position.slice(0, 4)
  }
}

/** Render position badges from positions[] array with legacy fallback */
function PositionBadges({ role }: { role: { positions?: string[]; position_type: string } }) {
  const pos = Array.isArray(role.positions) && role.positions.length > 0
    ? role.positions
    : Array.isArray(role.positions) && role.positions.length === 0
      ? []  // citizen
      : [role.position_type]  // legacy fallback

  if (pos.length === 0) {
    return <span className="font-body text-caption px-1 py-0.5 rounded bg-base text-text-secondary/50">Citizen</span>
  }

  return (
    <span className="flex gap-0.5">
      {pos.map(p => (
        <span key={p} className={`font-body text-caption font-medium px-1 py-0.5 rounded text-center ${positionBadgeClass(p)}`}>
          {positionLabel(p)}
        </span>
      ))}
    </span>
  )
}

function formatTimer(seconds: number): string {
  if (seconds < 0) return 'OVERTIME'
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

/* -------------------------------------------------------------------------- */
/*  Component                                                                 */
/* -------------------------------------------------------------------------- */

export function FacilitatorDashboard() {
  const { id: simId } = useParams<{ id: string }>()
  const navigate = useNavigate()

  // Clear stale request queue on mount
  useEffect(() => { requestQueue.reset() }, [])

  /* State ----------------------------------------------------------------- */
  const [roles, setRoles] = useState<SimRunRole[]>([])
  const [keyEvents, setKeyEvents] = useState<KeyEvent[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [remaining, setRemaining] = useState<number | null>(null)
  const [actionLoading, setActionLoading] = useState<string | null>(null)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  /* Realtime hooks — replace manual channels + polling -------------------- */
  const { data: simRunRT, loading: simRunLoading } = useRealtimeRow<SimRun>('sim_runs', simId)
  // Load ALL recent pending_actions (not just status=pending) so confirmed cards stay visible for result display
  const { data: allPendingActions } = useRealtimeTable<PendingAction>(
    'pending_actions', simId,
    { orderBy: 'submitted_at.desc', limit: 20 },
  )
  // Filter for display: show pending + recently approved/rejected (last 30s)
  const pendingActions = allPendingActions.filter(pa =>
    pa.status === 'pending' ||
    (pa.resolved_at && Date.now() - new Date(pa.resolved_at as string).getTime() < 30000)
  )
  const { data: events } = useRealtimeTable<ObservatoryEvent>(
    'observatory_events', simId,
    { orderBy: 'created_at.desc', limit: 100 },
  )

  // Nuclear flight banner — subscribe to active nuclear actions
  const { data: nuclearActions } = useRealtimeTable<Record<string, unknown>>(
    'nuclear_actions', simId,
    { columns: 'id,status,country_code,timer_started_at,timer_duration_sec,payload' },
  )
  const flightAction = nuclearActions.find(a => a.status === 'awaiting_interception')
  const [flightCountdown, setFlightCountdown] = useState<number|null>(null)
  useEffect(() => {
    if (!flightAction) { setFlightCountdown(null); return }
    const started = new Date(flightAction.timer_started_at as string).getTime()
    const dur = Number(flightAction.timer_duration_sec || 600)
    const tick = () => {
      const rem = Math.max(0, dur - (Date.now() - started) / 1000)
      setFlightCountdown(rem)
    }
    tick()
    const iv = setInterval(tick, 1000)
    return () => clearInterval(iv)
  }, [flightAction])

  // Leadership votes — moderator sees live tally
  const { data: leadershipVotes } = useRealtimeTable<Record<string, unknown>>(
    'leadership_votes', simId ?? undefined,
    { columns: '*' },
  )
  const activeLeaderVotes = leadershipVotes.filter(v => v.status === 'voting') as {
    id:string; phase:string; country_code:string; votes:Record<string,string>;
    required_majority:number; expires_at:string|null; target_role:string;
    initiated_by:string;
  }[]

  // Leadership vote countdowns (one timer per active vote)
  const [leaderTimers, setLeaderTimers] = useState<Record<string, number>>({})
  useEffect(() => {
    if (activeLeaderVotes.length === 0) { setLeaderTimers({}); return }
    const tick = () => {
      const t: Record<string, number> = {}
      for (const lv of activeLeaderVotes) {
        if (lv.expires_at) {
          t[lv.id] = Math.max(0, (new Date(lv.expires_at).getTime() - Date.now()) / 1000)
        }
      }
      setLeaderTimers(t)
    }
    tick()
    const iv = setInterval(tick, 1000)
    return () => clearInterval(iv)
  }, [activeLeaderVotes.map(v => v.id).join(',')])

  // ── Columbia Elections — moderator view ──────────────────────────────
  const { data: electionNominationsRaw } = useRealtimeTable<Record<string, unknown>>(
    'election_nominations', simId,
    { columns: '*' },
  )
  const electionNominations = electionNominationsRaw as unknown as {
    id:string; election_type:string; election_round:number; role_id:string; camp:string
  }[]

  const { data: electionVotesRaw, refetch: refetchElectionVotes } = useRealtimeTable<Record<string, unknown>>(
    'election_votes', simId,
    { columns: 'id,election_type,voter_role_id,candidate_role_id' },
  )
  const electionVotes = electionVotesRaw as unknown as {
    id:string; election_type:string; voter_role_id:string; candidate_role_id:string
  }[]

  const { data: electionResultsRaw } = useRealtimeTable<Record<string, unknown>>(
    'election_results', simId,
    { columns: '*' },
  )
  const electionResults = electionResultsRaw as unknown as {
    id:string; election_type:string; election_round:number; winner_role_id:string|null;
    participant_votes:Record<string,number>; total_votes:Record<string,number>;
    population_votes:Record<string,unknown>
  }[]

  const [electionResolving, setElectionResolving] = useState(false)
  const [localVoteOverrides, setLocalVoteOverrides] = useState<Record<string, string | null>>({})

  // Derive active election events from key_events + current round
  const elecRound = simRunRT?.current_round ?? 0
  const electionKeyEvents = keyEvents.filter(e => e.type === 'election') as unknown as {
    type:string; subtype:string; round:number; nominations_round:number; name:string; country_code?:string
  }[]
  const activeNomEvent = electionKeyEvents.find(e => e.nominations_round === elecRound)
  const activeElecEvent = electionKeyEvents.find(e => e.round === elecRound)

  // Election stats for moderator
  const elecNomCount = activeNomEvent
    ? electionNominations.filter(n => n.election_type === activeNomEvent.subtype).length
    : 0
  const elecVoteCount = activeElecEvent
    ? electionVotes.filter(v => v.election_type === activeElecEvent.subtype).length
    : 0
  const elecResolved = activeElecEvent
    ? electionResults.find(r => r.election_type === activeElecEvent.subtype && r.election_round === activeElecEvent.round)
    : undefined
  // Moderator-visible vote tally (secret from participants, visible to moderator)
  const elecTallies: Record<string,number> = {}
  if (activeElecEvent) {
    electionVotes
      .filter(v => v.election_type === activeElecEvent.subtype)
      .forEach(v => { elecTallies[v.candidate_role_id] = (elecTallies[v.candidate_role_id] || 0) + 1 })
  }

  const handleResolveElection = async () => {
    if (!activeElecEvent || !simId) return
    setElectionResolving(true)
    try {
      // Determine contested seat for midterms
      const contestedSeat = activeElecEvent.subtype === 'parliamentary_midterm' ? 'shadow' : undefined
      await submitAction(simId, 'resolve_election', 'moderator', 'columbia', {
        election_type: activeElecEvent.subtype,
        contested_seat_role: contestedSeat,
      })
    } catch (e) { alert(e instanceof Error ? e.message : 'Resolution failed') }
    finally { setElectionResolving(false) }
  }

  // Auto-resolve nuclear launch when flight countdown reaches 0
  const nuclearResolving = useRef(false)
  useEffect(() => {
    if (!flightAction || flightCountdown === null || flightCountdown > 0) return
    if (nuclearResolving.current) return
    nuclearResolving.current = true
    const actionId = flightAction.id as string
    simAction(simId!, `nuclear/${actionId}/resolve`).catch(e =>
      console.error('Nuclear auto-resolve failed:', e)
    ).finally(() => { nuclearResolving.current = false })
  }, [flightCountdown, flightAction, simId])

  const simRun = simRunRT

  /* Derive simState from the realtime sim_runs row ----------------------- */
  const simState: SimState | null = simRun ? {
    status: simRun.status,
    current_round: simRun.current_round,
    current_phase: simRun.current_phase,
    phase_started_at: simRun.started_at,
    phase_duration_seconds: (simRun.schedule as Record<string, number>)?.phase_a_minutes
      ? (simRun.schedule as Record<string, number>).phase_a_minutes * 60
      : 3600,
    mode: 'manual',
    paused: simRun.status === 'paused',
    pending_actions: [],
  } : null

  /* One-time data loading (roles, key_events) — not polled --------------- */
  const loadRoles = useCallback(async () => {
    if (!simId) return
    try {
      const runRoles = await getSimRunRoles(simId)
      setRoles(runRoles)
      setError(null)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load simulation')
    } finally {
      setLoading(false)
    }
  }, [simId])

  useEffect(() => {
    loadRoles()
    // Retry after 3s if still loading (auth token may not be ready on first render)
    const retry = setTimeout(() => {
      if (loading) loadRoles()
    }, 3000)
    return () => clearTimeout(retry)
  }, [loadRoles])

  // Sync key_events from the realtime sim_runs row
  useEffect(() => {
    if (simRun?.key_events && Array.isArray(simRun.key_events)) {
      setKeyEvents(simRun.key_events as KeyEvent[])
    }
  }, [simRun?.key_events])

  // Update loading state once sim_run is resolved
  useEffect(() => {
    if (!simRunLoading && simRun) setLoading(false)
    else if (!simRunLoading && !simRun && simId) {
      setError('Simulation not found')
      setLoading(false)
    }
  }, [simRunLoading, simRun, simId])

  /* Timer countdown ------------------------------------------------------- */
  useEffect(() => {
    if (timerRef.current) clearInterval(timerRef.current)

    if (!simState?.phase_started_at || simState.paused) {
      setRemaining(null)
      return
    }

    const tick = () => {
      const now = Date.now()
      const started = new Date(simState.phase_started_at!).getTime()
      const elapsed = (now - started) / 1000
      const rem = simState.phase_duration_seconds - elapsed
      setRemaining(rem)
    }

    tick()
    timerRef.current = setInterval(tick, 1000)
    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [simState?.phase_started_at, simState?.phase_duration_seconds, simState?.paused])

  /* Phase control actions ------------------------------------------------- */
  const doAction = async (action: string, params?: Record<string, unknown>) => {
    if (!simId) return
    setActionLoading(action)
    try {
      await simAction(simId, action, params)
      // Realtime hooks will pick up DB changes automatically — no manual reload needed
    } catch (e) {
      alert(e instanceof Error ? e.message : 'Action failed')
    } finally {
      setActionLoading(null)
    }
  }

  /* Derived data ---------------------------------------------------------- */
  const currentStatus = simState?.status ?? simRun?.status ?? 'setup'
  const currentRound = simState?.current_round ?? simRun?.current_round ?? 0
  const currentPhase = simState?.current_phase ?? simRun?.current_phase ?? 'pre'
  const isPaused = simState?.paused ?? false
  const mode = simState?.mode ?? 'manual'
  const aiRoles = roles.filter((r) => r.is_ai_operated)
  const humanRoles = roles.filter((r) => !r.is_ai_operated)
  const roundKeyEvents = keyEvents.filter((e) => e.round === currentRound)

  /* Timer progress (0..1) ------------------------------------------------- */
  const timerProgress =
    simState?.phase_duration_seconds && remaining !== null
      ? Math.max(0, Math.min(1, 1 - remaining / simState.phase_duration_seconds))
      : 0

  /* Loading / Error states ------------------------------------------------ */
  if (loading) {
    return (
      <div className="min-h-screen bg-base">
        <Header subtitle="Live Simulation" />
        <main className="max-w-6xl mx-auto px-6 py-12">
          <p className="font-body text-body text-text-secondary">Loading simulation...</p>
        </main>
      </div>
    )
  }

  if (error || !simRun) {
    return (
      <div className="min-h-screen bg-base">
        <Header subtitle="Live Simulation" />
        <main className="max-w-6xl mx-auto px-6 py-12">
          <div className="bg-card border border-danger/30 rounded-lg p-6">
            <p className="font-body text-body text-danger">{error ?? 'Simulation not found'}</p>
            <button
              onClick={() => navigate('/dashboard')}
              className="mt-4 font-body text-body-sm text-action hover:underline"
            >
              Back to Dashboard
            </button>
          </div>
        </main>
      </div>
    )
  }

  /* Render ---------------------------------------------------------------- */
  return (
    <div className="min-h-screen bg-base flex flex-col">
      <Header subtitle="Live Simulation" />

      {/* Nuclear flight banner */}
      {flightAction && flightCountdown !== null && (
        <div style={{
          position:'sticky',top:0,zIndex:50,
          backgroundColor:'rgba(220,38,38,0.95)',padding:'0.75rem 1.5rem',
          display:'flex',alignItems:'center',justifyContent:'center',gap:'1rem',
          fontFamily:'JetBrains Mono, monospace',color:'white',
          animation:'pulse 2s ease-in-out infinite',
        }}>
          <span style={{fontSize:'1.1rem'}}>⚠ BALLISTIC MISSILE LAUNCH DETECTED — {(flightAction.country_code as string).toUpperCase()}</span>
          <span style={{fontSize:'1.3rem',fontWeight:700}}>
            {Math.floor(flightCountdown/60).toString().padStart(2,'0')}:{Math.floor(flightCountdown%60).toString().padStart(2,'0')}
          </span>
          <button
            onClick={() => {
              if (!confirm('RESOLVE NUCLEAR IMPACT NOW?\n\nThis will skip remaining interception time and resolve the strike immediately.')) return
              simAction(simId!, `nuclear/${flightAction.id as string}/resolve`).catch(e =>
                alert('Resolve failed: ' + e)
              )
            }}
            style={{
              marginLeft:'1rem',padding:'0.4rem 1rem',borderRadius:'0.25rem',
              backgroundColor:'white',color:'#991B1B',fontWeight:700,fontSize:'0.85rem',
              border:'none',cursor:'pointer',textTransform:'uppercase',letterSpacing:'0.05em',
            }}
          >RESOLVE NOW</button>
        </div>
      )}

      {/* ================================================================== */}
      {/*  TOP BAR — fixed control strip                                     */}
      {/* ================================================================== */}
      <div className="sticky top-0 z-30 bg-card border-b border-border px-6 py-3">
        {/* Row 1: Round + Phase + Timer + Controls */}
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-4">
            <span className="font-data text-data-lg text-text-primary">
              R{currentRound}
            </span>
            <span
              className={`font-body text-body-sm font-medium px-3 py-1 rounded-full ${phaseBadgeClass(currentPhase, isPaused)}`}
            >
              {phaseLabel(currentPhase, isPaused)}
            </span>
            {remaining !== null && (
              <span
                className={`font-data text-data-lg ${
                  remaining < 0 ? 'text-danger animate-pulse' : 'text-text-primary'
                }`}
              >
                {formatTimer(remaining)}
              </span>
            )}
          </div>

          <div className="flex items-center gap-2">
            <ControlButton
              label="Back"
              prefix="◄"
              onClick={() => doAction('phase/back')}
              loading={actionLoading === 'phase/back'}
              variant="secondary"
            />
            {isPaused ? (
              <ControlButton
                label="Resume"
                onClick={() => doAction('resume')}
                loading={actionLoading === 'resume'}
                variant="primary"
              />
            ) : (
              <ControlButton
                label="Pause"
                onClick={() => doAction('pause')}
                loading={actionLoading === 'pause'}
                variant="warning"
              />
            )}
            {currentStatus === 'setup' || currentStatus === 'pre_start' ? (
              <ControlButton
                label="▶ Start Simulation"
                onClick={async () => {
                  if (!simId) return
                  setActionLoading('start')
                  try {
                    // If in setup, move to pre_start first
                    if (currentStatus === 'setup') {
                      await simAction(simId, 'pre-start')
                    }
                    // Then start the simulation
                    await simAction(simId, 'start')
                    // Realtime hooks will pick up state changes
                  } catch (e) {
                    alert(e instanceof Error ? e.message : 'Start failed')
                  } finally {
                    setActionLoading(null)
                  }
                }}
                loading={actionLoading === 'start'}
                variant="primary"
              />
            ) : (
              <ControlButton
                label="Next Phase"
                suffix="▸"
                onClick={() => doAction('phase/end')}
                loading={actionLoading === 'phase/end'}
                variant="primary"
              />
            )}
            <ControlButton
              label="+5m"
              onClick={() => doAction('phase/extend', { minutes: 5 })}
              loading={actionLoading === 'phase/extend'}
              variant="secondary"
            />
            <ControlButton
              label="End Sim"
              onClick={() => {
                if (confirm('End this simulation? This cannot be undone.')) {
                  doAction('end')
                }
              }}
              loading={actionLoading === 'end'}
              variant="danger"
            />
            <ControlButton
              label="Restart"
              onClick={async () => {
                if (confirm('RESTART simulation? All runtime data (events, decisions, world state changes) will be deleted. Only initial setup preserved.')) {
                  await doAction('restart')
                  window.location.reload()
                }
              }}
              loading={actionLoading === 'restart'}
              variant="danger"
            />
            {currentRound >= 1 && (
              <ControlButton
                label={`↺ R${currentRound}`}
                onClick={async () => {
                  if (confirm(`Restart Round ${currentRound}? All events, actions, and meetings from this round will be deleted. Phase A will restart with fresh timer.`)) {
                    await doAction('restart-round')
                    window.location.reload()
                  }
                }}
                loading={actionLoading === 'restart-round'}
                variant="secondary"
              />
            )}
            {currentRound > 1 && (
              <ControlButton
                label={`← R${currentRound - 1}`}
                onClick={() => {
                  const target = currentRound - 1
                  if (confirm(`Roll back to Round ${target}? All data from Round ${currentRound} will be deleted.`)) {
                    simAction(simId!, 'rollback', { target_round: target })
                  }
                }}
                loading={actionLoading === 'rollback'}
                variant="secondary"
              />
            )}
          </div>
        </div>

        {/* Row 2: Progress bar + Mode + LLM */}
        <div className="flex items-center justify-between">
          <div className="flex-1 mr-6">
            <div className="w-full bg-border rounded-full h-2">
              <div
                className={`h-2 rounded-full transition-all duration-1000 ${
                  remaining !== null && remaining < 0 ? 'bg-danger' : 'bg-action'
                }`}
                style={{ width: `${Math.min(100, timerProgress * 100)}%` }}
              />
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <span className="font-body text-caption text-text-secondary">Mode:</span>
              <button
                onClick={() => {
                  const newMode = mode === 'manual' ? 'automatic' : 'manual'
                  doAction('mode', {
                    auto_advance: newMode === 'automatic',
                    auto_approve: newMode === 'automatic',
                  })
                }}
                className={`font-body text-caption font-medium px-2 py-0.5 rounded ${
                  mode === 'manual'
                    ? 'bg-text-secondary/10 text-text-secondary'
                    : 'bg-success/10 text-success'
                }`}
              >
                {mode === 'manual' ? 'Manual' : 'Automatic'}
              </button>
            </div>
            <div className="flex items-center gap-1">
              <span className="font-body text-caption text-text-secondary">LLM:</span>
              <span className="w-2 h-2 rounded-full bg-success inline-block" />
              <span className="font-body text-caption text-success">ok</span>
            </div>
          </div>
        </div>
      </div>

      {/* ================================================================== */}
      {/*  MAIN CONTENT                                                      */}
      {/* ================================================================== */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-6 py-6">
        {/* Post-sim banner */}
        {(currentStatus === 'completed' || currentStatus === 'aborted') && (
          <div className={`rounded-lg p-6 border mb-6 ${
            currentStatus === 'completed' ? 'bg-success/5 border-success/30' : 'bg-danger/5 border-danger/30'
          }`}>
            <h2 className="font-heading text-h2 text-text-primary mb-2">
              Simulation {currentStatus === 'completed' ? 'Complete' : 'Aborted'}
            </h2>
            <div className="flex items-center gap-6 font-data text-data text-text-secondary">
              <span>Rounds played: {currentRound}</span>
              <span>Events: {events.length}</span>
              <span>Participants: {humanRoles.length} human / {aiRoles.length} AI</span>
            </div>
          </div>
        )}

        {/* Sim title */}
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-heading text-h2 text-text-primary">{simRun.name}</h2>
          <button
            onClick={() => navigate(`/sim/${simId}/edit`)}
            className="font-body text-caption text-action hover:underline"
          >
            Edit Setup
          </button>
        </div>

        {/* Special Moments banner (context-sensitive, above columns) */}
        {roundKeyEvents.length > 0 && (
          <div className="mb-4">
            <DashboardSection title={`This Round: Special Events`} highlight>
              <div className="flex flex-wrap gap-2">
                {roundKeyEvents.map((ke, idx) => (
                  <span
                    key={idx}
                    className={`font-body text-caption border rounded-full px-3 py-1 ${
                      ke.type === 'election' ? 'bg-warning/10 text-warning border-warning/20' :
                      'bg-accent/10 text-accent border-accent/20'
                    }`}
                  >
                    {ke.name || ke.description || `${ke.type}: ${ke.subtype || ''}`}
                  </span>
                ))}
              </div>
            </DashboardSection>
          </div>
        )}

        {/* ============================================================ */}
        {/*  TWO-COLUMN LAYOUT                                            */}
        {/* ============================================================ */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

          {/* ── LEFT COLUMN: Moderator Actions ───────────────────────── */}
          <div className="space-y-6">
            {/* Pending Actions + Auto-approve */}
            <DashboardSection
              title="Pending Actions"
              badge={pendingActions.length > 0 ? String(pendingActions.length) : undefined}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="font-body text-caption text-text-secondary">
                  Actions requiring your approval
                </span>
                <button
                  onClick={() => {
                    const newAuto = !simRun?.auto_approve
                    if (newAuto && !confirm('ENABLE AUTO-APPROVE?\n\nAll pending actions (assassination, arrest, change_leader) will be automatically confirmed without moderator review.\n\nThis is intended for testing and AI-only runs.')) return
                    doAction('mode', { auto_advance: false, auto_approve: newAuto })
                  }}
                  className={`relative inline-flex items-center gap-2 font-body text-caption font-bold uppercase tracking-wider px-3 py-1 rounded border transition-all ${
                    simRun?.auto_approve
                      ? 'bg-danger/30 text-danger border-danger/60 shadow-[0_0_8px_rgba(220,38,38,0.4)] animate-pulse'
                      : 'bg-text-secondary/5 text-text-secondary border-border hover:border-text-secondary/40'
                  }`}
                >
                  <span className={`w-2 h-2 rounded-full ${
                    simRun?.auto_approve ? 'bg-danger' : 'bg-text-secondary/40'
                  }`} />
                  {simRun?.auto_approve ? 'AUTO' : 'Manual'}
                </button>
                <button
                  onClick={() => {
                    const newVal = !simRun?.auto_attack
                    doAction('mode', { auto_advance: false, auto_approve: simRun?.auto_approve ?? false, auto_attack: newVal, dice_mode: simRun?.dice_mode ?? false })
                  }}
                  className={`relative inline-flex items-center gap-2 font-body text-caption font-bold uppercase tracking-wider px-3 py-1 rounded border transition-all ${
                    simRun?.auto_attack
                      ? 'bg-danger/30 text-danger border-danger/60 shadow-[0_0_8px_rgba(220,38,38,0.4)] animate-pulse'
                      : 'bg-text-secondary/5 text-text-secondary border-border hover:border-text-secondary/40'
                  }`}
                >
                  <span className={`w-2 h-2 rounded-full ${
                    simRun?.auto_attack ? 'bg-danger' : 'bg-text-secondary/40'
                  }`} />
                  {simRun?.auto_attack ? 'Auto-Attack' : 'Attack: Manual'}
                </button>
                <button
                  onClick={() => {
                    const newVal = !simRun?.dice_mode
                    doAction('mode', { auto_advance: false, auto_approve: simRun?.auto_approve ?? false, auto_attack: simRun?.auto_attack ?? false, dice_mode: newVal })
                  }}
                  className={`relative inline-flex items-center gap-2 font-body text-caption font-bold uppercase tracking-wider px-3 py-1 rounded border transition-all ${
                    simRun?.dice_mode
                      ? 'bg-danger/30 text-danger border-danger/60 shadow-[0_0_8px_rgba(220,38,38,0.4)] animate-pulse'
                      : 'bg-text-secondary/5 text-text-secondary border-border hover:border-text-secondary/40'
                  }`}
                >
                  <span className={`w-2 h-2 rounded-full ${
                    simRun?.dice_mode ? 'bg-danger' : 'bg-text-secondary/40'
                  }`} />
                  {simRun?.dice_mode ? 'Dice: REAL' : 'Dice: Auto'}
                </button>
              </div>
              {pendingActions.length === 0 && !activeNomEvent && !activeElecEvent && activeLeaderVotes.length === 0 ? (
                <EmptyState message="No pending actions" />
              ) : (
                <div className="space-y-2 max-h-[500px] overflow-y-auto pr-1">
                  {pendingActions.map((pa) => (
                    <PendingActionCard key={pa.id} pa={pa} simRun={simRun}
                      onConfirm={async (rolls) => {
                        const res = await simAction(simId!, `pending/${pa.id}/confirm`, rolls ? {precomputed_rolls: rolls} : {})
                        return res
                      }}
                      onReject={() => doAction(`pending/${pa.id}/reject`)} />
                  ))}
                  {/* Leadership change votes — moderator sees live tally + confirm */}
                  {activeLeaderVotes.map(lv => {
                    const votes = lv.votes || {}
                    const voters = Object.entries(votes)
                    const voteCount = voters.length
                    const isRemoval = lv.phase === 'removal'
                    const yesCount = isRemoval ? voters.filter(([,v]) => v === 'yes').length : 0
                    const noCount = isRemoval ? voters.filter(([,v]) => v === 'no').length : 0
                    const majorityReached = isRemoval
                      ? yesCount >= lv.required_majority
                      : voters.some(([, cand]) => voters.filter(([,v]) => v === cand).length >= lv.required_majority)
                    // Election tallies
                    const tallies: Record<string, number> = {}
                    if (!isRemoval) voters.forEach(([,c]) => { tallies[c] = (tallies[c] || 0) + 1 })
                    const timer = leaderTimers[lv.id]
                    const timerStr = timer != null
                      ? `${Math.floor(timer/60)}:${String(Math.floor(timer%60)).padStart(2,'0')}`
                      : '--:--'

                    return (
                      <div key={lv.id} className={`border rounded-lg p-3 ${majorityReached ? 'bg-warning/15 border-warning/50' : 'bg-base border-border'}`}>
                        <div className="flex items-center justify-between mb-1">
                          <span className="font-data text-caption font-bold text-text-primary uppercase">
                            {isRemoval ? 'Remove HoS' : 'Elect HoS'} — {lv.country_code.toUpperCase()}
                          </span>
                          <span className={`font-data text-caption ${timer != null && timer < 60 ? 'text-danger' : 'text-text-secondary'}`}>
                            {timerStr}
                          </span>
                        </div>

                        <div className="font-body text-caption text-text-secondary mb-1">
                          Initiated by {lv.initiated_by} · Need {lv.required_majority}
                        </div>

                        <div className="font-data text-caption text-text-primary">
                          {isRemoval ? (
                            <div className="flex items-center gap-3">
                              <span><span className="text-danger font-bold">{yesCount}</span> YES</span>
                              <span><span className="text-success font-bold">{noCount}</span> NO</span>
                              <span className="text-text-secondary">({voteCount} voted)</span>
                              {voters.map(([rid, v]) => (
                                <span key={rid} className={`text-caption ${v === 'yes' ? 'text-danger' : 'text-success'}`} title={rid}>
                                  {rid.slice(0,8)}: {v}
                                </span>
                              ))}
                            </div>
                          ) : (
                            <div className="flex flex-wrap gap-x-3 gap-y-0.5">
                              {Object.entries(tallies).sort((a,b) => b[1]-a[1]).map(([cand, cnt]) => (
                                <span key={cand}>
                                  <span className={cnt >= lv.required_majority ? 'text-action font-bold' : 'text-text-primary'}>{cand}</span>
                                  : {cnt}
                                </span>
                              ))}
                              {voteCount === 0 && <span className="text-text-secondary">No votes yet</span>}
                            </div>
                          )}
                        </div>

                        {majorityReached && !simRun?.auto_approve && (
                          <button onClick={() => {
                              const label = isRemoval ? 'Confirm HoS removal' : 'Confirm new HoS election'
                              if (!confirm(`${label} in ${lv.country_code.toUpperCase()}?`)) return
                              simAction(simId!, `leadership-votes/${lv.id}/resolve`)
                            }}
                            className="mt-2 font-body text-caption font-medium bg-action text-white px-3 py-1 rounded hover:bg-action/90 transition-colors">
                            {isRemoval ? 'Confirm Removal' : 'Confirm Election'}
                          </button>
                        )}
                        {majorityReached && simRun?.auto_approve && (
                          <span className="mt-2 inline-block font-body text-caption text-success">Auto-confirmed</span>
                        )}
                      </div>
                    )
                  })}

                  {/* Columbia Elections — Moderator Cards */}
                  {activeNomEvent && (() => {
                    const nomOpen = simRun?.nominations_open === true
                    const isAuto = simRun?.auto_approve
                    return (
                    <div className="border rounded-lg p-3 bg-action/5 border-action/30">
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-data text-caption font-bold text-action uppercase">
                          Columbia Nominations — {activeNomEvent.subtype === 'presidential' ? 'Presidential' : 'Mid-Term'}
                        </span>
                        <span className="font-data text-caption text-text-secondary">
                          R{activeNomEvent.nominations_round} → Election R{activeNomEvent.round}
                        </span>
                      </div>

                      {!nomOpen && !isAuto && (
                        <button onClick={async () => {
                          const { supabase: sb } = await import('@/lib/supabase')
                          await sb.from('sim_runs').update({
                            nominations_open: true,
                            nominations_closed: false,
                            election_open: false,
                            election_stopped: false,
                            election_started_at: null,
                            election_duration_min: null,
                            election_econ_score: null,
                            election_stability: null,
                            election_inflation: null,
                          }).eq('id', simId!)
                          setLocalVoteOverrides({})
                        }}
                          className="w-full font-body text-body-sm font-medium bg-action text-white py-2 rounded-lg hover:bg-action/90 transition-colors mb-2">
                          Start Nominations
                        </button>
                      )}

                      {(nomOpen || isAuto) && (() => {
                        const nomsClosed = simRun?.nominations_closed === true
                        const currentNoms = electionNominations.filter(n => n.election_type === activeNomEvent.subtype)
                        const columbiaRoles = roles.filter(r => r.country_code === 'columbia' && r.status === 'active')
                        const nominatedIds = new Set(currentNoms.map(n => n.role_id))
                        const availableToAdd = columbiaRoles.filter(r => !nominatedIds.has(r.id))

                        return nomsClosed ? (
                          <div className="bg-success/5 border border-success/20 rounded p-2 mt-1">
                            <span className="font-body text-caption text-success font-medium">
                              Nominations closed — {currentNoms.length} candidate{currentNoms.length !== 1 ? 's' : ''} approved for R{activeNomEvent.round} election
                            </span>
                          </div>
                        ) : (
                        <>
                          <div className="font-body text-caption text-text-secondary mb-1">
                            {elecNomCount} nominee{elecNomCount !== 1 ? 's' : ''} registered
                          </div>

                          {/* Nominee list with remove buttons */}
                          {currentNoms.length > 0 && (
                            <div className="bg-card border border-border rounded divide-y divide-border mt-1 mb-2">
                              {currentNoms.map(n => (
                                <div key={n.id} className="flex items-center justify-between px-3 py-1.5">
                                  <span className={`font-data text-caption capitalize ${
                                    n.camp === 'opposition' ? 'text-action' : 'text-text-primary'
                                  }`}>{n.role_id} <span className="text-text-secondary/50">({n.camp})</span></span>
                                  <button onClick={async () => {
                                    const { supabase: sb } = await import('@/lib/supabase')
                                    await sb.from('election_nominations').delete().eq('id', n.id)
                                  }} className="font-body text-caption text-danger/60 hover:text-danger transition-colors">
                                    remove
                                  </button>
                                </div>
                              ))}
                            </div>
                          )}

                          {/* Add nominee dropdown */}
                          {availableToAdd.length > 0 && (
                            <div className="flex gap-1 mb-2">
                              <select id="add-nominee-select" className="flex-1 font-body text-caption bg-base border border-border rounded px-2 py-1">
                                <option value="">Add nominee...</option>
                                {availableToAdd.map(r => (
                                  <option key={r.id} value={r.id}>{r.character_name} ({r.id})</option>
                                ))}
                              </select>
                              <button onClick={async () => {
                                const select = document.getElementById('add-nominee-select') as HTMLSelectElement
                                const rid = select?.value
                                if (!rid) return
                                const camp = ['tribune','challenger'].includes(rid) ? 'opposition' : 'president_camp'
                                const { supabase: sb } = await import('@/lib/supabase')
                                await sb.from('election_nominations').insert({
                                  sim_run_id: simId,
                                  election_type: activeNomEvent.subtype,
                                  election_round: activeNomEvent.round,
                                  role_id: rid,
                                  country_code: 'columbia',
                                  camp,
                                })
                                select.value = ''
                              }} className="font-body text-caption font-medium bg-action/10 text-action px-3 py-1 rounded hover:bg-action/20 transition-colors">
                                Add
                              </button>
                            </div>
                          )}

                          {elecNomCount === 0 && (
                            <div className="font-body text-caption text-text-secondary/50 mb-2">
                              Waiting for Columbia citizens to nominate...
                            </div>
                          )}

                          {/* Close & Approve button */}
                          <button onClick={async () => {
                            if (!confirm(`Close nominations with ${currentNoms.length} candidate${currentNoms.length !== 1 ? 's' : ''}?\n\nThis will finalize the candidate list for the R${activeNomEvent.round} election.`)) return
                            const { supabase: sb } = await import('@/lib/supabase')
                            await sb.from('sim_runs').update({ nominations_closed: true }).eq('id', simId!)
                          }}
                            disabled={currentNoms.length === 0}
                            className="w-full font-body text-caption font-medium bg-success/10 text-success py-1.5 rounded hover:bg-success/20 disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
                            Close and Approve Nominations ({currentNoms.length})
                          </button>
                        </>
                        )
                      })()}
                    </div>
                    )
                  })()}

                  {activeElecEvent && !elecResolved && (() => {
                    const elecStarted = simRun?.election_open === true
                    const elecStartedAt = simRun?.election_started_at ?? null
                    const elecDurationMin = simRun?.election_duration_min ?? 10

                    // Economy indicator for moderator
                    const colState = (() => {
                      const c = roles.find(r => r.country_code === 'columbia')
                      return c ? { stab: 0, infl: 0 } : { stab: 0, infl: 0 }
                    })()

                    return (
                    <div className="border rounded-lg p-3 bg-warning/10 border-warning/40">
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-data text-caption font-bold text-warning uppercase">
                          Columbia Election — {activeElecEvent.subtype === 'presidential' ? 'Presidential' : 'Mid-Term'}
                        </span>
                        <span className="font-data text-caption text-text-secondary">
                          R{activeElecEvent.round}
                        </span>
                      </div>

                      {(() => {
                        const OPPOSITION = new Set(['tribune', 'challenger'])
                        const ALL_VOTERS = ['dealer','volt','anchor','shadow','shield','tribune','challenger']
                        const candidates = electionNominations.filter(n => n.election_type === activeElecEvent.subtype)
                        // Build voter map: role_id -> candidate voted for (with local overrides)
                        const voterMap: Record<string,string> = {}
                        electionVotes.filter(v => v.election_type === activeElecEvent.subtype).forEach(v => {
                          voterMap[v.voter_role_id] = v.candidate_role_id
                        })
                        // Apply local overrides
                        for (const [rid, cid] of Object.entries(localVoteOverrides)) {
                          if (cid === null || cid === '') delete voterMap[rid]
                          else voterMap[rid] = cid
                        }
                        // Economy score — use cached from start, or treat as unknown
                        const econNote = simRun?.election_econ_score != null ? String(simRun.election_econ_score) : null
                        // If no cached score, we'll load it via ElectionEconIndicator
                        // For weight calc, default to bonus=true if unknown (conservative)
                        const hasBonus = econNote ? parseFloat(econNote) < 0.5 : true

                        return !elecStarted ? (
                        <>
                          <div className="font-body text-caption text-text-secondary mb-2">
                            {candidates.length} candidates ready. Start voting (10 min timer).
                          </div>
                          <button onClick={async () => {
                            // Load economy score at election start for display
                            const { supabase: sb } = await import('@/lib/supabase')
                            const { data: cs } = await sb.from('countries').select('stability,inflation').eq('sim_run_id', simId!).eq('id','columbia').limit(1)
                            const stab = cs?.[0]?.stability ?? 0
                            const infl = cs?.[0]?.inflation ?? 0
                            const eScore = Math.max(0, (stab - 2) / 10) * 0.45 + Math.max(0, 1 - infl / 12) * 0.55
                            const startedAt = new Date().toISOString()
                            await sb.from('sim_runs').update({
                              election_open: true,
                              election_started_at: startedAt,
                              election_duration_min: 10,
                              election_econ_score: parseFloat(eScore.toFixed(3)),
                              election_stability: parseFloat(Number(stab).toFixed(1)),
                              election_inflation: parseFloat(Number(infl).toFixed(1)),
                              election_stopped: false,
                            }).eq('id', simId!)
                          }}
                            className="w-full font-body text-body-sm font-medium bg-warning text-white py-2 rounded-lg hover:bg-warning/90 transition-colors">
                            Start Election
                          </button>
                        </>
                      ) : (
                        <>
                          {/* Timer or Closed label */}
                          {(() => {
                            const elapsed = elecStartedAt ? (Date.now() - new Date(elecStartedAt).getTime()) / 1000 : 0
                            const total = elecDurationMin * 60
                            const timerExpired = elecDurationMin > 0 && elapsed >= total
                            const stopped = simRun?.election_stopped === true || elecDurationMin === 0 || timerExpired

                            if (stopped) {
                              return (
                                <div className="bg-warning/10 border border-warning/30 rounded p-2 mb-1">
                                  <span className="font-body text-caption text-warning font-medium">Voting closed — {elecVoteCount} votes cast</span>
                                </div>
                              )
                            }
                            const rem = Math.max(0, total - elapsed)
                            const mm = String(Math.floor(rem / 60)).padStart(2, '0')
                            const ss = String(Math.floor(rem % 60)).padStart(2, '0')
                            return (
                              <div className="flex items-center justify-between mb-1">
                                <span className="font-data text-caption text-warning">{mm}:{ss}</span>
                                <button onClick={async () => {
                                  const { supabase: sb } = await import('@/lib/supabase')
                                  await sb.from('sim_runs').update({ election_duration_min: elecDurationMin + 5 }).eq('id', simId!)
                                }} className="font-body text-caption text-text-secondary hover:text-action px-1">+5m</button>
                              </div>
                            )
                          })()}

                          {/* Economy indicator — load live if not captured at start */}
                          <ElectionEconIndicator simId={simId!} simRun={simRun} />

                          {/* Voter table: role → vote dropdown → weight */}
                          <div className="bg-card border border-border rounded divide-y divide-border mb-2">
                            {ALL_VOTERS.map(rid => {
                              const voted = voterMap[rid]
                              const isOpp = OPPOSITION.has(rid)
                              const weight = isOpp ? (hasBonus ? 3 : 2) : 1
                              return (
                                <div key={rid} className="flex items-center gap-2 px-3 py-1.5 text-caption">
                                  <span className="font-body text-text-primary w-20 capitalize">{rid}</span>
                                  <select value={voted || ''} onChange={async (e) => {
                                    const newCandidate = e.target.value
                                    // Optimistic local update
                                    setLocalVoteOverrides(prev => ({ ...prev, [rid]: newCandidate || null }))
                                    // Persist to DB
                                    const { supabase: sb } = await import('@/lib/supabase')
                                    await sb.from('election_votes').delete()
                                      .eq('sim_run_id', simId!).eq('election_type', activeElecEvent.subtype).eq('voter_role_id', rid)
                                    if (newCandidate) {
                                      await sb.from('election_votes').insert({
                                        sim_run_id: simId, election_type: activeElecEvent.subtype,
                                        election_round: activeElecEvent.round, voter_role_id: rid,
                                        candidate_role_id: newCandidate, country_code: 'columbia',
                                      })
                                    }
                                  }}
                                    className="flex-1 font-body text-caption bg-base border border-border rounded px-1 py-0.5">
                                    <option value="">—</option>
                                    {candidates.map(c => (
                                      <option key={c.role_id} value={c.role_id}>{c.role_id}</option>
                                    ))}
                                  </select>
                                  <span className={`font-data w-4 text-right ${isOpp ? 'text-warning font-medium' : 'text-text-secondary'}`}>
                                    {weight}
                                  </span>
                                </div>
                              )
                            })}
                          </div>

                          {/* Candidate totals */}
                          {candidates.length > 0 && (
                            <div className="bg-base rounded p-2 mb-2">
                              <div className="font-body text-caption text-text-secondary mb-1">Weighted totals:</div>
                              <div className="flex gap-3">
                                {candidates.map(c => {
                                  const total = ALL_VOTERS.reduce((sum, rid) => {
                                    if (voterMap[rid] !== c.role_id) return sum
                                    const isOpp = OPPOSITION.has(rid)
                                    const w = isOpp ? (hasBonus ? 3 : 2) : 1
                                    return sum + w
                                  }, 0)
                                  const maxVotes = ALL_VOTERS.reduce((sum, rid) => {
                                    const isOpp = OPPOSITION.has(rid)
                                    return sum + (isOpp ? (hasBonus ? 3 : 2) : 1)
                                  }, 0)
                                  const majority = Math.floor(maxVotes / 2) + 1
                                  return (
                                    <span key={c.role_id} className={`font-data text-caption ${total >= majority ? 'text-success font-bold' : 'text-text-primary'}`}>
                                      <span className="capitalize">{c.role_id}</span>: {total}
                                    </span>
                                  )
                                })}
                                <span className="text-text-secondary/50 font-data text-caption ml-auto">
                                  simple majority
                                </span>
                              </div>
                            </div>
                          )}

                          {/* Single action button: Stop → Approve sequence */}
                          {(() => {
                            const elapsed = elecStartedAt ? (Date.now() - new Date(elecStartedAt).getTime()) / 1000 : 0
                            const total = elecDurationMin * 60
                            const timerDone = elecDurationMin > 0 && elapsed >= total
                            const isStopped = simRun?.election_stopped === true || elecDurationMin === 0 || timerDone

                            return (
                              <div className="flex gap-2">
                                {!isStopped ? (
                                  <button onClick={async () => {
                                      const { supabase: sb } = await import('@/lib/supabase')
                                      await sb.from('sim_runs').update({ election_stopped: true }).eq('id', simId!)
                                    }}
                                    className="flex-1 font-body text-caption font-medium bg-action text-white px-3 py-1.5 rounded hover:bg-action/90 transition-colors">
                                    Stop Voting
                                  </button>
                                ) : (
                                  <button onClick={handleResolveElection}
                                    disabled={electionResolving || elecVoteCount === 0}
                                    className="flex-1 font-body text-caption font-medium bg-action text-white px-3 py-1.5 rounded hover:bg-action/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
                                    {electionResolving ? 'Approving...' : 'Approve and Publish Results'}
                                  </button>
                                )}
                                <button onClick={async () => {
                                  if (!confirm('Restart election? All votes will be deleted.')) return
                                  const { supabase: sb } = await import('@/lib/supabase')
                                  await sb.from('election_votes').delete().eq('sim_run_id', simId!).eq('election_type', activeElecEvent.subtype)
                                  await sb.from('sim_runs').update({
                                    election_open: true,
                                    election_stopped: false,
                                    election_started_at: new Date().toISOString(),
                                    election_duration_min: 10,
                                  }).eq('id', simId!)
                                  setTimeout(() => refetchElectionVotes(), 500)
                                }}
                                  className="font-body text-caption font-medium bg-danger/10 text-danger px-3 py-1.5 rounded hover:bg-danger/20 transition-colors">
                                  Restart
                                </button>
                              </div>
                            )
                          })()}
                        </>
                      )
                      })()}
                    </div>
                    )
                  })()}

                  {elecResolved && activeElecEvent && (
                    <div className="border rounded-lg p-3 bg-success/10 border-success/30">
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-data text-caption font-bold text-success uppercase">
                          Election Result — {activeElecEvent.subtype === 'presidential' ? 'Presidential' : 'Mid-Term'}
                        </span>
                      </div>
                      <div className="font-body text-caption text-text-primary">
                        {elecResolved.winner_role_id
                          ? `Winner: ${elecResolved.winner_role_id}`
                          : 'No winner (tie or no majority)'}
                      </div>
                      {elecResolved.total_votes && (
                        <div className="font-data text-caption text-text-secondary mt-0.5">
                          Votes: {Object.entries(elecResolved.total_votes as Record<string,number>)
                            .sort((a,b) => b[1]-a[1])
                            .map(([c,n]) => `${c}: ${n}`)
                            .join(', ')}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </DashboardSection>

            {/* SIM Events Feed — two tabs: game events vs AI reflections */}
            <EventsFeedCard events={events} />


            {/* Participants & Role Assignment */}
            <ParticipantPanel simId={simId!} roles={roles} onRolesChanged={loadRoles} />
          </div>

          {/* ── RIGHT COLUMN: Monitoring & Tools ─────────────────────── */}
          <div className="space-y-6">
            {/* AI Participants — full observability dashboard */}
            <AIParticipantDashboard simId={simId!} />

            {/* Public Screen */}
            <DashboardSection title="Public Screen">
              <div className="flex items-center gap-3 flex-wrap">
                <button
                  onClick={() => window.open(`/screen/${simId}`, '_blank')}
                  className="font-body text-caption font-medium bg-action/10 text-action px-3 py-1 rounded hover:bg-action/20 transition-colors"
                >
                  View Public Screen
                </button>
                <button
                  onClick={() => { /* Broadcast */ }}
                  className="font-body text-caption font-medium bg-accent/10 text-accent px-3 py-1 rounded hover:bg-accent/20 transition-colors"
                >
                  Broadcast
                </button>
              </div>
            </DashboardSection>

            {/* Map & Data */}
            <DashboardSection title="Map & Data">
              <div className="flex items-center gap-3 flex-wrap">
                <button
                  onClick={() => window.open(`/map/deployments.html?sim_run_id=${simId}`, '_blank')}
                  className="font-body text-caption font-medium bg-action/10 text-action px-3 py-1 rounded hover:bg-action/20 transition-colors"
                >
                  Open Map
                </button>
                <button
                  onClick={() => navigate(`/sim/${simId}/edit`)}
                  className="font-body text-caption font-medium bg-text-secondary/10 text-text-secondary px-3 py-1 rounded hover:bg-text-secondary/20 transition-colors"
                >
                  Edit Setup
                </button>
              </div>
            </DashboardSection>

          </div>
        </div>
      </main>
    </div>
  )
}

/* -------------------------------------------------------------------------- */
/*  Sub-components                                                            */
/* -------------------------------------------------------------------------- */

/** Section wrapper with consistent styling. */
function DashboardSection({
  title,
  badge,
  highlight,
  children,
}: {
  title: string
  badge?: string
  highlight?: boolean
  children: React.ReactNode
}) {
  return (
    <section
      className={`bg-card border rounded-lg p-5 ${
        highlight ? 'border-accent/40' : 'border-border'
      }`}
    >
      <div className="flex items-center gap-2 mb-3">
        <h3 className="font-heading text-h3 text-text-primary">{title}</h3>
        {badge && (
          <span className="font-data text-caption bg-action/10 text-action px-2 py-0.5 rounded-full">
            {badge}
          </span>
        )}
      </div>
      {children}
    </section>
  )
}

/* ── Pending Action Card — combat resolution with dice input ────────────── */

const COMBAT_ACTIONS = new Set([
  'ground_attack','air_strike','naval_combat','naval_bombardment','naval_blockade','launch_missile_conventional',
])

const COMBAT_LABELS: Record<string,string> = {
  ground_attack:'Ground Attack', air_strike:'Air Strike', naval_combat:'Naval Combat',
  naval_bombardment:'Naval Bombardment', launch_missile_conventional:'Missile Launch',
}

function ElectionEconIndicator({ simId, simRun }: { simId: string; simRun: SimRun | null }) {
  const [econ, setEcon] = useState<{ stab: string; infl: string; score: string } | null>(null)

  useEffect(() => {
    // Use cached values from columns if available
    if (simRun?.election_stability && simRun?.election_inflation && simRun?.election_econ_score) {
      setEcon({ stab: String(simRun.election_stability), infl: String(simRun.election_inflation), score: String(simRun.election_econ_score) })
      return
    }
    // Otherwise load live
    supabase.from('countries').select('stability,inflation').eq('sim_run_id', simId).eq('id', 'columbia').limit(1)
      .then(({ data }) => {
        if (!data?.[0]) return
        const stab = data[0].stability ?? 0
        const infl = data[0].inflation ?? 0
        const sc = Math.max(0, (stab - 2) / 10) * 0.45 + Math.max(0, 1 - infl / 12) * 0.55
        setEcon({ stab: Number(stab).toFixed(1), infl: Number(infl).toFixed(1), score: sc.toFixed(3) })
      })
  }, [simId, simRun?.election_stability, simRun?.election_inflation, simRun?.election_econ_score])

  if (!econ) return null
  const scoreNum = parseFloat(econ.score)
  return (
    <div className="bg-base rounded p-2 mb-2 font-data text-caption">
      <div className="flex gap-3">
        <span className="text-text-secondary">Stability: <span className="text-text-primary">{econ.stab}</span></span>
        <span className="text-text-secondary">Inflation: <span className="text-text-primary">{econ.infl}%</span></span>
        <span className="text-text-secondary">Score: <span className={`font-medium ${scoreNum < 0.5 ? 'text-danger' : 'text-success'}`}>{econ.score}</span></span>
        <span className="text-text-secondary/50">Threshold: 0.50</span>
      </div>
    </div>
  )
}

function PendingActionCard({pa, simRun, onConfirm, onReject}:{
  pa: PendingAction; simRun: SimRun | null
  onConfirm: (rolls?: Record<string,unknown>) => Promise<Record<string,unknown>>; onReject: () => void
}) {
  const isCombat = COMBAT_ACTIONS.has(pa.action_type)
  const diceMode = simRun?.dice_mode ?? false
  const DICE_COMBAT = new Set(['ground_attack', 'naval_combat'])
  const needsDice = isCombat && diceMode && DICE_COMBAT.has(pa.action_type)
  const [expanded, setExpanded] = useState(false)
  const [diceValues, setDiceValues] = useState<Record<string,number>>({})
  const [combatResult, setCombatResult] = useState<Record<string,unknown>|null>(null)
  const [resolving, setResolving] = useState(false)
  const payload = pa.payload || {}

  // For ground combat: need attacker dice (up to 3) and defender dice (up to 2) per exchange
  // Simplified: moderator enters one set of dice, engine handles the rest
  const attackerUnits = (payload.attacker_unit_codes as string[])?.length ?? 1
  const defenderUnits = (payload._defender_ground_count as number) ?? 2
  const atkDiceCount = pa.action_type === 'ground_attack' ? Math.min(3, attackerUnits) : 1
  const defDiceCount = pa.action_type === 'ground_attack' ? Math.min(2, defenderUnits) : 1

  const setDie = (key: string, val: string) => {
    const n = parseInt(val)
    if (n >= 1 && n <= 6) setDiceValues(prev => ({...prev, [key]: n}))
    else if (val === '') setDiceValues(prev => {const c = {...prev}; delete c[key]; return c})
  }

  const allDiceFilled = needsDice && expanded
    ? Array.from({length: atkDiceCount}, (_,i) => `atk_${i}`).every(k => diceValues[k] >= 1 && diceValues[k] <= 6)
      && Array.from({length: defDiceCount}, (_,i) => `def_${i}`).every(k => diceValues[k] >= 1 && diceValues[k] <= 6)
    : true

  const handleConfirmWithDice = async () => {
    setResolving(true)
    try {
      let rolls: Record<string,unknown> | undefined
      if (needsDice) {
        const atkRolls = Array.from({length: atkDiceCount}, (_,i) => diceValues[`atk_${i}`] || 1)
        const defRolls = Array.from({length: defDiceCount}, (_,i) => diceValues[`def_${i}`] || 1)
        if (pa.action_type === 'ground_attack') {
          rolls = {attacker: [atkRolls], defender: [defRolls]}
        } else if (pa.action_type === 'naval_combat') {
          rolls = {attacker: atkRolls[0], defender: defRolls[0]}
        }
      }
      const res = await onConfirm(rolls)
      if (isCombat) setCombatResult(res)
      if (!isCombat) setActionDone('approved')
    } catch(e) {
      alert(e instanceof Error ? e.message : 'Failed')
    } finally {
      setResolving(false)
    }
  }

  const [actionDone, setActionDone] = useState<'approved'|'rejected'|null>(null)

  const handleQuickConfirm = async (e?: React.MouseEvent) => {
    e?.stopPropagation()
    if (resolving || actionDone) return
    setResolving(true)
    try {
      await onConfirm()
      setActionDone('approved')
    } catch { /* ignore */ }
    finally { setResolving(false) }
  }

  const handleQuickReject = (e?: React.MouseEvent) => {
    e?.stopPropagation()
    if (resolving || actionDone) return
    setActionDone('rejected')
    onReject()
  }

  // Already resolved — show brief result then fade
  if (actionDone) {
    return (
      <div className={`flex items-center justify-between rounded-lg px-4 py-3 border transition-opacity ${
        actionDone === 'approved' ? 'bg-success/10 border-success/30' : 'bg-danger/10 border-danger/30'
      }`}>
        <span className={`font-body text-body-sm font-medium ${actionDone === 'approved' ? 'text-success' : 'text-danger'}`}>
          {actionDone === 'approved' ? 'Approved' : 'Rejected'} — {pa.action_type}
        </span>
        <span className="font-body text-caption text-text-secondary">
          {pa.target_info || pa.country_code}
        </span>
      </div>
    )
  }

  // Non-combat: simple card with loading state
  if (!isCombat) {
    return (
      <div className="flex items-center justify-between bg-base rounded-lg px-4 py-3 border border-border">
        <div>
          <span className="font-body text-body-sm text-text-primary font-medium">{pa.action_type}</span>
          <span className="font-body text-caption text-text-secondary ml-2">
            {pa.target_info || `${pa.role_id} (${pa.country_code})`}
          </span>
        </div>
        <div className="flex gap-2">
          <button onClick={() => handleQuickConfirm()} disabled={resolving}
            className="font-body text-caption font-medium bg-success/10 text-success px-3 py-1 rounded hover:bg-success/20 disabled:opacity-50 transition-colors">
            {resolving ? '...' : 'Confirm'}
          </button>
          <button onClick={() => handleQuickReject()} disabled={resolving}
            className="font-body text-caption font-medium bg-danger/10 text-danger px-3 py-1 rounded hover:bg-danger/20 disabled:opacity-50 transition-colors">
            Reject
          </button>
        </div>
      </div>
    )
  }

  // Combat card
  const targetRow = payload.target_row as number
  const targetCol = payload.target_col as number

  return (
    <div className="bg-base rounded-lg border border-danger/30 overflow-hidden">
      {/* Header — always visible */}
      <div className="flex items-center justify-between px-4 py-3 cursor-pointer hover:bg-danger/5" onClick={() => setExpanded(!expanded)}>
        <div className="flex items-center gap-2">
          <span className="font-body text-caption font-bold text-danger uppercase">{COMBAT_LABELS[pa.action_type] ?? pa.action_type}</span>
          <span className="font-body text-caption text-text-primary">{pa.country_code}</span>
          {targetRow && <span className="font-data text-caption text-text-secondary">→ ({targetRow},{targetCol})</span>}
          {needsDice && <span className="font-body text-caption text-warning bg-warning/10 px-1.5 py-0.5 rounded">DICE</span>}
        </div>
        <div className="flex items-center gap-2">
          {!expanded && !needsDice && (
            <>
              <button onClick={(e) => handleQuickConfirm(e)} disabled={resolving}
                className="font-body text-caption font-medium bg-success/10 text-success px-3 py-1 rounded hover:bg-success/20 disabled:opacity-50 transition-colors">
                {resolving ? '...' : 'Confirm'}
              </button>
              <button onClick={(e) => handleQuickReject(e)} disabled={resolving}
                className="font-body text-caption font-medium bg-danger/10 text-danger px-3 py-1 rounded hover:bg-danger/20 disabled:opacity-50 transition-colors">
                Reject
              </button>
            </>
          )}
          <span className="font-body text-caption text-text-secondary">{expanded ? '▲' : '▼'}</span>
        </div>
      </div>

      {/* Expanded: combat details + dice input */}
      {expanded && (
        <div className="border-t border-border px-4 py-3 space-y-3">
          {/* Details */}
          <div className="grid grid-cols-3 gap-3 text-caption font-body">
            <div><span className="text-text-secondary block">Attacker</span><span className="text-text-primary font-medium">{pa.country_code}</span></div>
            <div><span className="text-text-secondary block">Target</span><span className="font-data text-danger">({targetRow},{targetCol})</span></div>
            <div><span className="text-text-secondary block">Units</span>
              <span className="font-data text-text-primary">
                {(payload.attacker_unit_codes as string[])?.join(', ') || payload.attacker_unit_code as string || '?'}
              </span>
            </div>
          </div>

          {/* Modifiers */}
          {payload._modifiers && (
            <div className="grid grid-cols-2 gap-3 text-caption font-body">
              <div>
                <span className="text-text-secondary">Atk mod: </span>
                {(payload._modifiers as {attacker:{label:string;value:number}[];defender:{label:string;value:number}[]}).attacker.length > 0
                  ? (payload._modifiers as {attacker:{label:string;value:number}[]}).attacker.map((m,i) =>
                      <span key={i} className={m.value > 0 ? 'text-success' : 'text-danger'}> {m.label} {m.value > 0 ? '+' : ''}{m.value}</span>
                    )
                  : <span className="text-text-secondary/50">none</span>
                }
              </div>
              <div>
                <span className="text-text-secondary">Def mod: </span>
                {(payload._modifiers as {attacker:{label:string;value:number}[];defender:{label:string;value:number}[]}).defender.length > 0
                  ? (payload._modifiers as {defender:{label:string;value:number}[]}).defender.map((m,i) =>
                      <span key={i} className={m.value > 0 ? 'text-success' : 'text-danger'}> {m.label} {m.value > 0 ? '+' : ''}{m.value}</span>
                    )
                  : <span className="text-text-secondary/50">none</span>
                }
              </div>
            </div>
          )}

          {/* Dice input — only for ground/naval in dice mode */}
          {needsDice && (pa.action_type === 'ground_attack' || pa.action_type === 'naval_combat') ? (
            <div className="space-y-2">
              <div className="bg-warning/5 border border-warning/20 rounded p-2">
                <span className="font-body text-caption text-warning font-medium">Roll physical dice and enter results:</span>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <span className="font-body text-caption text-text-secondary block mb-1">
                    Attacker ({atkDiceCount} {atkDiceCount===1?'die':'dice'})
                  </span>
                  <div className="flex gap-2">
                    {Array.from({length: atkDiceCount}, (_,i) => (
                      <input key={`atk_${i}`} type="number" min={1} max={6}
                        value={diceValues[`atk_${i}`] ?? ''}
                        onChange={e => setDie(`atk_${i}`, e.target.value)}
                        className="w-12 h-10 text-center font-data text-data-lg bg-base border border-border rounded focus:border-action focus:outline-none"
                        placeholder="?" />
                    ))}
                  </div>
                </div>
                <div>
                  <span className="font-body text-caption text-text-secondary block mb-1">
                    Defender ({defDiceCount} {defDiceCount===1?'die':'dice'})
                  </span>
                  <div className="flex gap-2">
                    {Array.from({length: defDiceCount}, (_,i) => (
                      <input key={`def_${i}`} type="number" min={1} max={6}
                        value={diceValues[`def_${i}`] ?? ''}
                        onChange={e => setDie(`def_${i}`, e.target.value)}
                        className="w-12 h-10 text-center font-data text-data-lg bg-base border border-border rounded focus:border-action focus:outline-none"
                        placeholder="?" />
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ) : needsDice ? (
            <div className="bg-base border border-border rounded p-2">
              <span className="font-body text-caption text-text-secondary">
                {pa.action_type === 'air_strike' ? 'Air strike uses probability — no dice needed.' :
                 pa.action_type === 'naval_bombardment' ? 'Bombardment uses probability — no dice needed.' :
                 'This combat type uses auto-generated rolls.'}
              </span>
            </div>
          ) : null}

          {/* Action buttons */}
          <div className="flex gap-2 pt-1">
            <button onClick={handleConfirmWithDice}
              disabled={resolving || (needsDice && (pa.action_type === 'ground_attack' || pa.action_type === 'naval_combat') && !allDiceFilled)}
              className="font-body text-caption font-bold uppercase bg-success/10 text-success px-4 py-2 rounded hover:bg-success/20 transition-colors disabled:opacity-40 disabled:cursor-not-allowed">
              {resolving ? 'Resolving...' : needsDice ? 'Resolve with Dice' : 'Confirm Attack'}
            </button>
            {!combatResult && <button onClick={onReject}
              className="font-body text-caption font-medium bg-danger/10 text-danger px-3 py-2 rounded hover:bg-danger/20 transition-colors">
              Reject
            </button>}
          </div>

          {/* Combat outcome */}
          {combatResult && (
            <div className={`mt-2 p-3 rounded border ${combatResult.attacker_won ? 'bg-success/5 border-success/20' : 'bg-danger/5 border-danger/20'}`}>
              <h4 className={`font-body text-caption font-bold uppercase ${combatResult.attacker_won ? 'text-success' : 'text-danger'}`}>
                {combatResult.attacker_won ? 'Attacker Victory' : 'Defender Holds'}
              </h4>
              <p className="font-body text-caption text-text-primary mt-1">{String(combatResult.narrative??'')}</p>
              {(combatResult.captured as {unit_id:string;type:string;from:string}[]||[]).length > 0 && (
                <p className="font-body text-caption text-action mt-1">
                  Captured: {(combatResult.captured as {unit_id:string;type:string;from:string}[]).map(c=>`${c.type} (${c.from})`).join(', ')}
                </p>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

/** Grey empty state with a message. */
function EmptyState({ message }: { message: string }) {
  return (
    <p className="font-body text-body-sm text-text-secondary py-2">{message}</p>
  )
}

/** Participant & Role Assignment Panel — assign users to roles, toggle AI/human. */
function ParticipantPanel({
  simId,
  roles,
  onRolesChanged,
}: {
  simId: string
  roles: SimRunRole[]
  onRolesChanged: () => void
}) {
  const [open, setOpen] = useState(false)
  const [users, setUsers] = useState<UserRecord[]>([])
  const [usersLoaded, setUsersLoaded] = useState(false)

  // Include arrested roles in the management view (they're still "in the game")
  const activeRoles = roles.filter((r) => r.status === 'active' || r.status === 'arrested')
  const humanRoles = activeRoles.filter((r) => !r.is_ai_operated)
  const aiRoles = activeRoles.filter((r) => r.is_ai_operated)
  const assignedHuman = humanRoles.filter((r) => r.user_id)
  const unassignedHuman = humanRoles.filter((r) => !r.user_id)

  // Group roles by country
  const byCountry = activeRoles.reduce((acc, r) => {
    acc[r.country_code] = acc[r.country_code] || []
    acc[r.country_code].push(r)
    return acc
  }, {} as Record<string, SimRunRole[]>)

  const loadUsers = async () => {
    if (usersLoaded) return
    try {
      const all = await getAllUsers()
      setUsers(all.filter((u) => u.status === 'active'))
      setUsersLoaded(true)
    } catch {
      setUsers([])
    }
  }

  const handleAssign = async (roleId: string, userId: string | null, roleName: string) => {
    const userName = userId ? users.find((u) => u.id === userId)?.display_name ?? 'user' : 'nobody'
    const msg = userId
      ? `Assign ${userName} to ${roleName}?`
      : `Unassign ${roleName}?`
    if (!confirm(msg)) return
    try {
      await assignUserToRole(simId, roleId, userId)
      onRolesChanged()
    } catch (e) {
      alert(e instanceof Error ? e.message : 'Assignment failed')
    }
  }

  const handleToggleAI = async (roleId: string, isAI: boolean, roleName: string) => {
    const msg = isAI
      ? `Switch ${roleName} to AI-operated?`
      : `Switch ${roleName} to Human?`
    if (!confirm(msg)) return
    try {
      await toggleRoleAI(simId, roleId, isAI)
      onRolesChanged()
    } catch (e) {
      alert(e instanceof Error ? e.message : 'Toggle failed')
    }
  }

  // Users not assigned to any role in this sim
  const assignedUserIds = new Set(roles.filter((r) => r.user_id).map((r) => r.user_id))
  const availableUsers = users.filter((u) => !assignedUserIds.has(u.id))

  return (
    <DashboardSection
      title="Participants"
      badge={`${assignedHuman.length}/${humanRoles.length} assigned`}
    >
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-4 font-data text-caption text-text-secondary">
          <span>{humanRoles.length} human</span>
          <span>{aiRoles.length} AI</span>
          <span>{unassignedHuman.length} unassigned</span>
        </div>
        <button
          onClick={() => {
            setOpen(!open)
            if (!open) loadUsers()
          }}
          className="font-body text-caption text-action hover:underline"
        >
          {open ? 'Hide assignments' : 'Manage Assignments'}
        </button>
      </div>

      {open && (
        <div className="space-y-3 mt-3">
          {Object.entries(byCountry)
            .sort(([a], [b]) => a.localeCompare(b))
            .map(([countryId, countryRoles]) => (
              <div key={countryId} className="bg-base rounded-lg border border-border p-3">
                <h4 className="font-heading text-caption text-text-primary font-medium mb-2 uppercase tracking-wider">
                  {countryId}
                </h4>
                <div className="space-y-1">
                  {countryRoles.map((role) => (
                    <div
                      key={role.id}
                      className="flex items-center gap-3 py-1"
                    >
                      <span className="font-body text-caption text-text-primary w-24 shrink-0">
                        {role.character_name}
                      </span>
                      <span className="w-24 shrink-0">
                        {role.status === 'arrested'
                          ? <span className="font-body text-caption font-medium px-1.5 py-0.5 rounded bg-danger/15 text-danger">Arrested</span>
                          : <PositionBadges role={role} />
                        }
                      </span>

                      {/* AI/Human toggle */}
                      <button
                        onClick={() => handleToggleAI(role.id, !role.is_ai_operated, role.character_name)}
                        className={`font-body text-caption px-2 py-0.5 rounded shrink-0 ${
                          role.is_ai_operated
                            ? 'bg-accent/10 text-accent'
                            : 'bg-success/10 text-success'
                        }`}
                      >
                        {role.is_ai_operated ? 'AI' : 'Human'}
                      </button>

                      {/* User assignment dropdown (human roles only) */}
                      {!role.is_ai_operated && (
                        <select
                          value={role.user_id ?? ''}
                          onChange={(e) =>
                            handleAssign(role.id, e.target.value || null, role.character_name)
                          }
                          className="flex-1 bg-card border border-border rounded px-2 py-1 font-body text-caption text-text-primary min-w-0"
                        >
                          <option value="">— unassigned —</option>
                          {/* Show currently assigned user first */}
                          {role.user_id && (
                            <option value={role.user_id}>
                              {users.find((u) => u.id === role.user_id)?.display_name ??
                                role.user_id.slice(0, 8)}
                            </option>
                          )}
                          {availableUsers.map((u) => (
                            <option key={u.id} value={u.id}>
                              {u.display_name} ({u.email})
                            </option>
                          ))}
                        </select>
                      )}

                      {/* View as participant (opens their interface in proxy mode) */}
                      <button
                        onClick={() => window.open(`/play/${simId}?role=${role.id}`, '_blank')}
                        className="font-body text-caption text-action hover:underline shrink-0"
                        title={`View as ${role.character_name}`}
                      >
                        view
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            ))}
        </div>
      )}
    </DashboardSection>
  )
}


/** Top bar control button with consistent styling. */
function ControlButton({
  label,
  prefix,
  suffix,
  onClick,
  loading,
  variant,
}: {
  label: string
  prefix?: string
  suffix?: string
  onClick: () => void
  loading?: boolean
  variant: 'primary' | 'secondary' | 'warning' | 'danger'
}) {
  const base = 'font-body text-caption font-medium px-3 py-1.5 rounded transition-colors disabled:opacity-50'
  const variants: Record<string, string> = {
    primary: 'bg-action text-white hover:bg-action/90',
    secondary: 'bg-text-secondary/10 text-text-secondary hover:bg-text-secondary/20',
    warning: 'bg-warning/10 text-warning hover:bg-warning/20',
    danger: 'bg-danger/10 text-danger hover:bg-danger/20',
  }

  return (
    <button
      onClick={onClick}
      disabled={!!loading}
      className={`${base} ${variants[variant]}`}
    >
      {loading ? (
        '...'
      ) : (
        <>
          {prefix && <span className="mr-1">{prefix}</span>}
          {label}
          {suffix && <span className="ml-1">{suffix}</span>}
        </>
      )}
    </button>
  )
}
