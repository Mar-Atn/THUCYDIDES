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
  getSimRun,
  getSimRunRoles,
  getSimState,
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
  const [simRun, setSimRun] = useState<SimRun | null>(null)
  const [roles, setRoles] = useState<SimRunRole[]>([])
  const [simState, setSimState] = useState<SimState | null>(null)
  const [events, setEvents] = useState<ObservatoryEvent[]>([])
  const [keyEvents, setKeyEvents] = useState<KeyEvent[]>([])
  const [pendingActions, setPendingActions] = useState<PendingAction[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [remaining, setRemaining] = useState<number | null>(null)
  const [actionLoading, setActionLoading] = useState<string | null>(null)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  /* Data loading ---------------------------------------------------------- */
  const loadData = useCallback(async () => {
    if (!simId) return
    try {
      const [run, runRoles] = await Promise.all([
        getSimRun(simId),
        getSimRunRoles(simId),
      ])
      if (!run) {
        setError('Simulation not found')
        setLoading(false)
        return
      }
      setSimRun(run)
      setRoles(runRoles)

      // Try loading state from API — graceful fallback
      try {
        const state = (await getSimState(simId)) as unknown as SimState
        setSimState(state)
      } catch {
        // API not available yet — build state from sim_run
        setSimState({
          status: run.status,
          current_round: run.current_round,
          current_phase: run.current_phase,
          phase_started_at: run.started_at,
          phase_duration_seconds: run.schedule?.phase_a_minutes
            ? run.schedule.phase_a_minutes * 60
            : 3600,
          mode: 'manual',
          paused: false,
          pending_actions: [],
        })
      }

      // Load observatory events
      try {
        const { data: evts } = await supabase
          .from('observatory_events')
          .select('*')
          .eq('sim_run_id', simId)
          .order('created_at', { ascending: false })
          .limit(50)
        setEvents((evts ?? []) as ObservatoryEvent[])
      } catch {
        setEvents([])
      }

      // Load pending actions
      try {
        const { data: pa } = await supabase
          .from('pending_actions')
          .select('*')
          .eq('sim_run_id', simId)
          .eq('status', 'pending')
          .order('submitted_at', { ascending: false })
        setPendingActions((pa ?? []) as PendingAction[])
      } catch {
        setPendingActions([])
      }

      // Load key events from sim run
      if (run.key_events && Array.isArray(run.key_events)) {
        setKeyEvents(run.key_events as KeyEvent[])
      }

      setError(null)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load simulation')
    } finally {
      setLoading(false)
    }
  }, [simId])

  useEffect(() => {
    loadData()
  }, [loadData])

  /* Supabase Realtime subscriptions --------------------------------------- */
  useEffect(() => {
    if (!simId) return

    // Channel 1: sim_runs changes — phase transitions, timer, status
    const simRunChannel = supabase
      .channel(`sim_run:${simId}`)
      .on(
        'postgres_changes',
        {
          event: 'UPDATE',
          schema: 'public',
          table: 'sim_runs',
          filter: `id=eq.${simId}`,
        },
        (payload) => {
          const row = payload.new as Record<string, unknown>
          if (row) {
            // Update sim run state directly from realtime payload
            setSimRun((prev) => prev ? { ...prev, ...row } as SimRun : prev)
            setSimState((prev) => ({
              status: (row.status as string) ?? prev?.status ?? 'setup',
              current_round: (row.current_round as number) ?? prev?.current_round ?? 0,
              current_phase: (row.current_phase as string) ?? prev?.current_phase ?? 'pre',
              phase_started_at: (row.phase_started_at as string | null) ?? prev?.phase_started_at ?? null,
              phase_duration_seconds: (row.phase_duration_seconds as number) ?? prev?.phase_duration_seconds ?? 3600,
              mode: prev?.mode ?? 'manual',
              paused: (row.status as string) === 'paused',
              pending_actions: prev?.pending_actions ?? [],
            }))
          }
        },
      )
      .subscribe()

    // Channel 2: observatory_events inserts — live action feed
    const eventsChannel = supabase
      .channel(`events:${simId}`)
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'observatory_events',
          filter: `sim_run_id=eq.${simId}`,
        },
        (payload) => {
          const newEvent = payload.new as ObservatoryEvent
          if (newEvent) {
            setEvents((prev) => [newEvent, ...prev].slice(0, 100))
          }
        },
      )
      .subscribe()

    // Channel 3: pending_actions changes — confirmation queue
    const pendingChannel = supabase
      .channel(`pending:${simId}`)
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'pending_actions',
          filter: `sim_run_id=eq.${simId}`,
        },
        () => {
          // Reload pending actions on any change (insert, update, delete)
          supabase
            .from('pending_actions')
            .select('*')
            .eq('sim_run_id', simId)
            .eq('status', 'pending')
            .order('submitted_at', { ascending: false })
            .then(({ data }) => setPendingActions((data ?? []) as PendingAction[]))
        },
      )
      .subscribe()

    // Fallback poll every 30s for resilience (connection drops, missed events)
    const fallbackInterval = setInterval(loadData, 30000)

    return () => {
      supabase.removeChannel(simRunChannel)
      supabase.removeChannel(eventsChannel)
      supabase.removeChannel(pendingChannel)
      clearInterval(fallbackInterval)
    }
  }, [simId, loadData])

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
      await loadData()
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
                    await loadData()
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
              onClick={() => {
                if (confirm('RESTART simulation? All runtime data (events, decisions, world state changes) will be deleted. Only initial setup preserved.')) {
                  doAction('restart')
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
                    simAction(simId!, 'rollback', { target_round: target }).then(() => loadData())
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
                    if (newAuto && !confirm('Enable AUTO-APPROVE? All pending actions will be automatically confirmed.')) return
                    doAction('mode', { auto_advance: false, auto_approve: newAuto })
                  }}
                  className={`font-body text-caption font-medium px-2 py-0.5 rounded ${
                    simRun?.auto_approve
                      ? 'bg-danger/20 text-danger'
                      : 'bg-text-secondary/10 text-text-secondary'
                  }`}
                >
                  {simRun?.auto_approve ? 'AUTO' : 'Manual'}
                </button>
              </div>
              {pendingActions.length === 0 ? (
                <EmptyState message="No pending actions" />
              ) : (
                <div className="space-y-2">
                  {pendingActions.map((pa) => (
                    <div
                      key={pa.id}
                      className="flex items-center justify-between bg-base rounded-lg px-4 py-3 border border-border"
                    >
                      <div>
                        <span className="font-body text-body-sm text-text-primary font-medium">
                          {pa.action_type}
                        </span>
                        <span className="font-body text-caption text-text-secondary ml-2">
                          {pa.target_info || `${pa.role_id} (${pa.country_code})`}
                        </span>
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={() => doAction(`pending/${pa.id}/confirm`)}
                          className="font-body text-caption font-medium bg-success/10 text-success px-3 py-1 rounded hover:bg-success/20 transition-colors"
                        >
                          Confirm
                        </button>
                        <button
                          onClick={() => doAction(`pending/${pa.id}/reject`)}
                          className="font-body text-caption font-medium bg-danger/10 text-danger px-3 py-1 rounded hover:bg-danger/20 transition-colors"
                        >
                          Reject
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </DashboardSection>

            {/* SIM Events Feed (fixed height, scrollable) */}
            <DashboardSection title="SIM Events" badge={events.length > 0 ? String(events.length) : undefined}>
              {events.length === 0 ? (
                <EmptyState message="No events yet" />
              ) : (
                <div className="space-y-1 h-80 overflow-y-auto">
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
            </DashboardSection>

            {/* Participants & Role Assignment */}
            <ParticipantPanel simId={simId!} roles={roles} onRolesChanged={loadData} />
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
                  onClick={() => { /* M8 */ }}
                  className="font-body text-caption font-medium bg-action/10 text-action px-3 py-1 rounded hover:bg-action/20 transition-colors"
                >
                  View
                </button>
                <button
                  onClick={() => { /* M8 */ }}
                  className="font-body text-caption font-medium bg-text-secondary/10 text-text-secondary px-3 py-1 rounded hover:bg-text-secondary/20 transition-colors"
                >
                  Customize
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
                  onClick={() => window.open('/map/viewer.html', '_blank')}
                  className="font-body text-caption font-medium bg-action/10 text-action px-3 py-1 rounded hover:bg-action/20 transition-colors"
                >
                  Open Map
                </button>
                <button
                  onClick={() => window.open('/map/deployments.html', '_blank')}
                  className="font-body text-caption font-medium bg-action/10 text-action px-3 py-1 rounded hover:bg-action/20 transition-colors"
                >
                  Deployments
                </button>
                <button
                  onClick={() => navigate(`/sim/${simId}/edit`)}
                  className="font-body text-caption font-medium bg-text-secondary/10 text-text-secondary px-3 py-1 rounded hover:bg-text-secondary/20 transition-colors"
                >
                  Edit Setup
                </button>
              </div>
            </DashboardSection>

            {/* Test Action Panel */}
            <TestActionPanel simId={simId!} roles={roles} onActionSubmitted={loadData} />
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
