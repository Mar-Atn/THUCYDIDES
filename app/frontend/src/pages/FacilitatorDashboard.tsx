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
  type SimRun,
  type SimRunRole,
} from '@/lib/queries'
import { supabase } from '@/lib/supabase'

/* -------------------------------------------------------------------------- */
/*  Types                                                                     */
/* -------------------------------------------------------------------------- */

interface SimState {
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
  action_type: string
  submitted_by: string
  target: string
  submitted_at: string
}

interface ObservatoryEvent {
  id: string
  sim_run_id: string
  round: number
  phase: string
  event_type: string
  category: string
  role_name: string | null
  description: string
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

  /* Poll state every 5 seconds ------------------------------------------- */
  useEffect(() => {
    if (!simId) return
    const interval = setInterval(loadData, 5000)
    return () => clearInterval(interval)
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
  const currentRound = simState?.current_round ?? simRun?.current_round ?? 0
  const currentPhase = simState?.current_phase ?? simRun?.current_phase ?? 'pre'
  const isPaused = simState?.paused ?? false
  const mode = simState?.mode ?? 'manual'
  const pendingActions = simState?.pending_actions ?? []
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
            <ControlButton
              label="Next Phase"
              suffix="▸"
              onClick={() => doAction('phase/end')}
              loading={actionLoading === 'phase/end'}
              variant="primary"
            />
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
                  /* Toggle placeholder — will call API */
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
      <main className="flex-1 max-w-6xl mx-auto w-full px-6 py-6 space-y-6">
        {/* Sim title */}
        <div className="flex items-center justify-between">
          <h2 className="font-heading text-h2 text-text-primary">{simRun.name}</h2>
          <button
            onClick={() => navigate(`/sim/${simId}/edit`)}
            className="font-body text-caption text-action hover:underline"
          >
            Edit Setup
          </button>
        </div>

        {/* -------------------------------------------------------------- */}
        {/*  Pending Actions                                                */}
        {/* -------------------------------------------------------------- */}
        <DashboardSection title="Pending Actions" badge={pendingActions.length > 0 ? String(pendingActions.length) : undefined}>
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
                      {pa.submitted_by} &rarr; {pa.target}
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

        {/* -------------------------------------------------------------- */}
        {/*  SIM Events Feed                                                */}
        {/* -------------------------------------------------------------- */}
        <DashboardSection title="SIM Events" badge={events.length > 0 ? String(events.length) : undefined}>
          {events.length === 0 ? (
            <EmptyState message="No events yet — actions will appear here as participants submit them" />
          ) : (
            <div className="space-y-1 max-h-80 overflow-y-auto">
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
                    {evt.description}
                  </span>
                  <span
                    className={`font-body text-caption font-medium px-2 py-0.5 rounded shrink-0 ${categoryBadgeClass(evt.category)}`}
                  >
                    {evt.category?.toUpperCase().slice(0, 4) ?? '---'}
                  </span>
                </div>
              ))}
            </div>
          )}
        </DashboardSection>

        {/* -------------------------------------------------------------- */}
        {/*  AI Participants                                                */}
        {/* -------------------------------------------------------------- */}
        <DashboardSection title="AI Participants" badge={aiRoles.length > 0 ? String(aiRoles.length) : undefined}>
          {aiRoles.length === 0 ? (
            <EmptyState message="No AI participants assigned to this simulation" />
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
                      ({role.status === 'active' ? 'idle' : role.status})
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

        {/* -------------------------------------------------------------- */}
        {/*  Participants                                                   */}
        {/* -------------------------------------------------------------- */}
        <DashboardSection title="Participants">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <span className="font-data text-data text-text-primary">
                {humanRoles.length} human
              </span>
              <span className="text-text-secondary">/</span>
              <span className="font-data text-data text-text-primary">
                {aiRoles.length} AI
              </span>
            </div>
            <button
              onClick={() => {
                /* Placeholder — participant assignment page */
              }}
              className="font-body text-caption text-action hover:underline"
            >
              Manage Assignments
            </button>
          </div>
        </DashboardSection>

        {/* -------------------------------------------------------------- */}
        {/*  Public Screen                                                  */}
        {/* -------------------------------------------------------------- */}
        <DashboardSection title="Public Screen">
          <div className="flex items-center gap-3">
            <button
              onClick={() => {
                /* Placeholder — open public screen preview */
              }}
              className="font-body text-caption font-medium bg-action/10 text-action px-3 py-1 rounded hover:bg-action/20 transition-colors"
            >
              View
            </button>
            <button
              onClick={() => {
                /* Placeholder — customize public screen */
              }}
              className="font-body text-caption font-medium bg-text-secondary/10 text-text-secondary px-3 py-1 rounded hover:bg-text-secondary/20 transition-colors"
            >
              Customize
            </button>
            <button
              onClick={() => {
                /* Placeholder — broadcast message */
              }}
              className="font-body text-caption font-medium bg-accent/10 text-accent px-3 py-1 rounded hover:bg-accent/20 transition-colors"
            >
              Broadcast Message
            </button>
          </div>
        </DashboardSection>

        {/* -------------------------------------------------------------- */}
        {/*  Map                                                            */}
        {/* -------------------------------------------------------------- */}
        <DashboardSection title="Map">
          <div className="flex items-center gap-3">
            <button
              onClick={() => {
                /* Placeholder — open map viewer */
              }}
              className="font-body text-caption font-medium bg-action/10 text-action px-3 py-1 rounded hover:bg-action/20 transition-colors"
            >
              Open Map
            </button>
            <button
              onClick={() => {
                /* Placeholder — open deployments */
              }}
              className="font-body text-caption font-medium bg-text-secondary/10 text-text-secondary px-3 py-1 rounded hover:bg-text-secondary/20 transition-colors"
            >
              Open Deployments
            </button>
          </div>
        </DashboardSection>

        {/* -------------------------------------------------------------- */}
        {/*  Explore SIM Data                                               */}
        {/* -------------------------------------------------------------- */}
        <DashboardSection title="Explore SIM Data">
          <div className="flex items-center gap-3">
            {['Countries', 'Relationships', 'Sanctions', 'All Tables'].map((label) => (
              <button
                key={label}
                onClick={() => {
                  /* Placeholder — open data view */
                }}
                className="font-body text-caption font-medium bg-action/10 text-action px-3 py-1 rounded hover:bg-action/20 transition-colors"
              >
                {label}
              </button>
            ))}
          </div>
        </DashboardSection>

        {/* -------------------------------------------------------------- */}
        {/*  Special Moments (context-sensitive)                            */}
        {/* -------------------------------------------------------------- */}
        {roundKeyEvents.length > 0 && (
          <DashboardSection title={`This Round: Special Events`} highlight>
            <div className="space-y-2">
              {roundKeyEvents.map((ke, idx) => (
                <div
                  key={idx}
                  className="flex items-center gap-3 bg-base rounded-lg px-4 py-3 border border-accent/30"
                >
                  <span className="font-body text-body-sm text-accent font-medium">
                    {ke.type}
                  </span>
                  <span className="font-body text-body-sm text-text-primary flex-1">
                    {ke.description}
                  </span>
                  {ke.country && (
                    <span className="font-body text-caption text-text-secondary">
                      {ke.country}
                    </span>
                  )}
                </div>
              ))}
            </div>
          </DashboardSection>
        )}
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
