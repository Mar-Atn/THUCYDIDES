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
  description: string
  country?: string
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

function positionBadgeClass(position: string): string {
  switch (position) {
    case 'head_of_state':
      return 'bg-warning/15 text-warning'
    case 'military_chief':
      return 'bg-danger/15 text-danger'
    case 'economy_officer':
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
    case 'military_chief': return 'Military'
    case 'economy_officer': return 'Economy'
    case 'diplomat': return 'Diplomat'
    case 'security': return 'Security'
    case 'opposition': return 'Opposition'
    default: return position
  }
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
                    className="font-body text-caption bg-accent/10 text-accent border border-accent/20 rounded-full px-3 py-1"
                  >
                    {ke.type}: {ke.description}
                    {ke.country && ` (${ke.country})`}
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
              {pendingActions.length === 0 ? (
                <EmptyState message="No pending actions" />
              ) : (
                <div className="space-y-2 max-h-[500px] overflow-y-auto pr-1">
                  {pendingActions.map((pa) => (
                    <PendingActionCard key={pa.id} pa={pa} simRun={simRun}
                      onConfirm={async (rolls) => {
                        // Use fetch directly to avoid race with realtime hook removing this card
                        const token = (await supabase.auth.getSession()).data.session?.access_token
                        const resp = await fetch(`/api/sim/${simId}/pending/${pa.id}/confirm`, {
                          method: 'POST',
                          headers: {'Content-Type': 'application/json', ...(token ? {'Authorization': `Bearer ${token}`} : {})},
                          body: JSON.stringify(rolls ? {precomputed_rolls: rolls} : {}),
                        })
                        if (!resp.ok) throw new Error((await resp.json().catch(()=>({}))).detail || 'Confirm failed')
                        const data = await resp.json()
                        return data.data
                      }}
                      onReject={() => doAction(`pending/${pa.id}/reject`)} />
                  ))}
                </div>
              )}
            </DashboardSection>

            {/* SIM Events Feed (tall, scrollable — stock exchange monitor) */}
            <div className="bg-card border border-border rounded-lg p-5">
              <div className="flex items-center gap-2 mb-3">
                <h3 className="font-heading text-h3 text-text-primary">SIM Events</h3>
                {events.length > 0 && (
                  <span className="font-data text-caption bg-action/10 text-action px-2 py-0.5 rounded-full">
                    {events.length}
                  </span>
                )}
              </div>
              {events.length === 0 ? (
                <div className="min-h-[30vh] flex items-center justify-center">
                  <p className="font-body text-body-sm text-text-secondary">No events yet</p>
                </div>
              ) : (
                <div className="space-y-1 min-h-[30vh] max-h-[30vh] overflow-y-auto">
                  {events.map((evt) => (
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
                        {evt.role_name ?? '---'}
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

            {/* Test Action Panel */}
            <TestActionPanel simId={simId!} roles={roles} onActionSubmitted={loadRoles} />

            {/* Participants & Role Assignment */}
            <ParticipantPanel simId={simId!} roles={roles} onRolesChanged={loadRoles} />
          </div>

          {/* ── RIGHT COLUMN: Monitoring & Tools ─────────────────────── */}
          <div className="space-y-6">
            {/* AI Participants */}
            <DashboardSection title="AI Participants" badge={aiRoles.length > 0 ? String(aiRoles.length) : undefined}>
              {aiRoles.length === 0 ? (
                <EmptyState message="No AI participants" />
              ) : (
                <>
                  <div className="flex flex-wrap gap-2 mb-3">
                    {aiRoles.map((role) => (
                      <span
                        key={role.id}
                        className="font-body text-caption bg-base border border-border rounded-full px-3 py-1 text-text-primary"
                      >
                        {role.character_name}{' '}
                        <span className="text-text-secondary">
                          ({role.country_id})
                        </span>
                      </span>
                    ))}
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => doAction('ai/trigger')}
                      className="font-body text-caption font-medium bg-action/10 text-action px-3 py-1 rounded hover:bg-action/20 transition-colors"
                    >
                      Trigger Now
                    </button>
                    <button
                      onClick={() => doAction('ai/pause-all')}
                      className="font-body text-caption font-medium bg-text-secondary/10 text-text-secondary px-3 py-1 rounded hover:bg-text-secondary/20 transition-colors"
                    >
                      Pause All
                    </button>
                  </div>
                </>
              )}
            </DashboardSection>

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
    } catch(e) {
      alert(e instanceof Error ? e.message : 'Failed')
    } finally {
      setResolving(false)
    }
  }

  // Non-combat or auto-dice: simple card
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
          <button onClick={() => onConfirm()} className="font-body text-caption font-medium bg-success/10 text-success px-3 py-1 rounded hover:bg-success/20 transition-colors">Confirm</button>
          <button onClick={onReject} className="font-body text-caption font-medium bg-danger/10 text-danger px-3 py-1 rounded hover:bg-danger/20 transition-colors">Reject</button>
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
              <button onClick={(e) => {e.stopPropagation(); onConfirm()}} className="font-body text-caption font-medium bg-success/10 text-success px-3 py-1 rounded hover:bg-success/20">Confirm</button>
              <button onClick={(e) => {e.stopPropagation(); onReject()}} className="font-body text-caption font-medium bg-danger/10 text-danger px-3 py-1 rounded hover:bg-danger/20">Reject</button>
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

  const activeRoles = roles.filter((r) => r.status === 'active')
  const humanRoles = activeRoles.filter((r) => !r.is_ai_operated)
  const aiRoles = activeRoles.filter((r) => r.is_ai_operated)
  const assignedHuman = humanRoles.filter((r) => r.user_id)
  const unassignedHuman = humanRoles.filter((r) => !r.user_id)

  // Group roles by country
  const byCountry = activeRoles.reduce((acc, r) => {
    acc[r.country_id] = acc[r.country_id] || []
    acc[r.country_id].push(r)
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
                      <span className={`font-body text-caption font-medium w-28 shrink-0 px-1.5 py-0.5 rounded text-center ${positionBadgeClass(role.position_type)}`}>
                        {positionLabel(role.position_type)}
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

/** Test Action Panel — moderator submits actions as any role for testing.
 *  Loads actual action permissions from role_actions table per selected role. */
function TestActionPanel({
  simId,
  roles,
  onActionSubmitted,
}: {
  simId: string
  roles: SimRunRole[]
  onActionSubmitted: () => void
}) {
  const [open, setOpen] = useState(false)
  const [selectedRole, setSelectedRole] = useState('')
  const [actionType, setActionType] = useState('')
  const [roleActions, setRoleActions] = useState<string[]>([])
  const [content, setContent] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState<string | null>(null)

  const activeRoles = roles.filter((r) => r.status === 'active')
  const selectedRoleData = activeRoles.find((r) => r.id === selectedRole)

  // Load actual actions for the selected role from role_actions table
  useEffect(() => {
    if (!selectedRole || !simId) {
      setRoleActions([])
      setActionType('')
      return
    }
    supabase
      .from('role_actions')
      .select('action_id')
      .eq('sim_run_id', simId)
      .eq('role_id', selectedRole)
      .order('action_id')
      .then(({ data }) => {
        const actions = (data ?? []).map((r: { action_id: string }) => r.action_id)
        setRoleActions(actions)
        setActionType(actions[0] ?? '')
      })
  }, [selectedRole, simId])

  const handleSubmit = async () => {
    if (!selectedRole || !actionType) return
    setSubmitting(true)
    setResult(null)
    try {
      const params: Record<string, unknown> = {}
      if (actionType === 'public_statement' && content) {
        params.content = content
      }
      const res = await submitAction(
        simId, actionType, selectedRole,
        selectedRoleData?.country_id ?? '',
        params,
      )
      setResult(res.narrative as string ?? 'Action submitted')
      setContent('')
      onActionSubmitted()
    } catch (e) {
      setResult(e instanceof Error ? e.message : 'Failed')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <DashboardSection title="Test Action">
      <button
        onClick={() => setOpen(!open)}
        className="font-body text-caption text-action hover:underline mb-2"
      >
        {open ? 'Hide test panel' : 'Submit action as any role...'}
      </button>

      {open && (
        <div className="space-y-3 mt-2">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="font-body text-caption text-text-secondary block mb-1">Role</label>
              <select
                value={selectedRole}
                onChange={(e) => setSelectedRole(e.target.value)}
                className="w-full bg-base border border-border rounded px-3 py-2 font-body text-body-sm text-text-primary"
              >
                <option value="">Select role...</option>
                {activeRoles.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.character_name} ({r.country_id}) — {r.position_type}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="font-body text-caption text-text-secondary block mb-1">
                Action ({roleActions.length} available)
              </label>
              <select
                value={actionType}
                onChange={(e) => setActionType(e.target.value)}
                disabled={roleActions.length === 0}
                className="w-full bg-base border border-border rounded px-3 py-2 font-body text-body-sm text-text-primary disabled:opacity-50"
              >
                {roleActions.length === 0 ? (
                  <option value="">Select a role first...</option>
                ) : (
                  roleActions.map((a) => (
                    <option key={a} value={a}>{a}</option>
                  ))
                )}
              </select>
            </div>
          </div>

          {actionType === 'public_statement' && (
            <div>
              <label className="font-body text-caption text-text-secondary block mb-1">
                Statement content
              </label>
              <input
                type="text"
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="Enter statement text..."
                className="w-full bg-base border border-border rounded px-3 py-2 font-body text-body-sm text-text-primary"
              />
            </div>
          )}

          <div className="flex items-center gap-3">
            <button
              onClick={handleSubmit}
              disabled={!selectedRole || submitting}
              className="bg-action text-white font-body text-caption font-medium px-4 py-2 rounded hover:bg-action/90 disabled:opacity-50 transition-colors"
            >
              {submitting ? 'Submitting...' : 'Submit Action'}
            </button>
            {result && (
              <span className="font-body text-caption text-text-secondary">
                {result}
              </span>
            )}
          </div>
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
