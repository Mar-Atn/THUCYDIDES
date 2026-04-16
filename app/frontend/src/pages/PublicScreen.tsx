/**
 * Public Screen — the room's focal display during a live simulation.
 * Route: /screen/:id (no auth required — display only)
 *
 * Layout: Full screen, dark, no navigation.
 * Top: Round + Phase + Timer + Sim time mapping
 * Center: Global map (2:1) with attacks + units
 * Right: Doomsday indices (rotating with theater maps)
 * Bottom-left: Columbia vs Cathay power balance
 * Bottom: News ticker (scrolling events)
 */

import { useEffect, useState, useCallback, useRef } from 'react'
import { useParams } from 'react-router-dom'
import { supabase } from '@/lib/supabase'
import { getSimRun, type SimRun } from '@/lib/queries'

/* -------------------------------------------------------------------------- */
/*  Types                                                                     */
/* -------------------------------------------------------------------------- */

interface SimState {
  status: string
  current_round: number
  current_phase: string
  phase_started_at: string | null
  phase_duration_seconds: number | null
  max_rounds: number
}

interface PublicEvent {
  id: string
  event_type: string
  summary: string
  role_name: string | null
  category: string | null
  country_code: string | null
  created_at: string
}

interface DoomsdayIndices {
  geopolitical_tension: number
  economic_health: number
  nuclear_danger: number
  ai_race: number
  prev_geopolitical_tension: number
  prev_economic_health: number
  prev_nuclear_danger: number
  prev_ai_race: number
}

/* -------------------------------------------------------------------------- */
/*  Helpers                                                                   */
/* -------------------------------------------------------------------------- */

const ROUND_TO_DATE: Record<number, string> = {
  0: 'Pre-Sim',
  1: 'H2 2026',
  2: 'H1 2027',
  3: 'H2 2027',
  4: 'H1 2028',
  5: 'H2 2028',
  6: 'H1 2029',
  7: 'H2 2029',
  8: 'H1 2030',
}

function formatTimer(seconds: number): string {
  if (seconds < 0) return 'OVERTIME'
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

function phaseLabel(phase: string): string {
  switch (phase) {
    case 'A': return 'NEGOTIATIONS'
    case 'B': return 'PROCESSING'
    case 'inter_round': return 'INTER-ROUND'
    case 'pre': return 'PRE-START'
    case 'post': return 'POST-SIM'
    default: return phase.toUpperCase()
  }
}

function trendArrow(current: number, prev: number): string {
  if (current > prev) return '\u2191'  // ↑
  if (current < prev) return '\u2193'  // ↓
  return '\u2192'  // →
}

function trendColor(current: number, prev: number, dangerUp: boolean = true): string {
  const rising = current > prev
  if (dangerUp) return rising ? 'text-danger' : current < prev ? 'text-success' : 'text-text-secondary'
  return rising ? 'text-success' : current < prev ? 'text-danger' : 'text-text-secondary'
}

/* Significant event types for the news ticker */
const SIGNIFICANT_EVENTS = new Set([
  'ground_attack', 'air_strike', 'naval_combat', 'naval_bombardment', 'naval_blockade',
  'launch_missile_conventional', 'nuclear_test', 'nuclear_launch_initiate',
  'assassination', 'arrest', 'change_leader', 'change_leader_initiated',
  'change_leader_removal', 'change_leader_elected',
  'public_statement', 'set_sanctions', 'set_tariffs',
  'propose_agreement', 'sign_agreement',
  'phase_b_complete', 'ai_triggered',
  'martial_law', 'covert_operation',
])

/* -------------------------------------------------------------------------- */
/*  Component                                                                 */
/* -------------------------------------------------------------------------- */

export function PublicScreen() {
  const { id: simId } = useParams<{ id: string }>()

  const [simRun, setSimRun] = useState<SimRun | null>(null)
  const [simState, setSimState] = useState<SimState | null>(null)
  const [events, setEvents] = useState<PublicEvent[]>([])
  const [remaining, setRemaining] = useState<number | null>(null)
  const [indices, setIndices] = useState<DoomsdayIndices>({
    geopolitical_tension: 3, economic_health: 7, nuclear_danger: 1, ai_race: 3,
    prev_geopolitical_tension: 3, prev_economic_health: 7, prev_nuclear_danger: 1, prev_ai_race: 3,
  })
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const tickerRef = useRef<HTMLDivElement>(null)

  /* Load data ------------------------------------------------------------- */
  const loadData = useCallback(async () => {
    if (!simId) return
    try {
      const run = await getSimRun(simId)
      if (!run) return
      setSimRun(run)
      setSimState({
        status: run.status,
        current_round: run.current_round,
        current_phase: run.current_phase,
        phase_started_at: run.started_at,
        phase_duration_seconds: run.schedule?.phase_a_minutes ? run.schedule.phase_a_minutes * 60 : 3600,
        max_rounds: run.max_rounds,
      })

      // Load significant events
      const { data: evts } = await supabase
        .from('observatory_events')
        .select('id, event_type, summary, role_name, category, country_code, created_at')
        .eq('sim_run_id', simId)
        .order('created_at', { ascending: false })
        .limit(30)
      setEvents((evts ?? []) as PublicEvent[])
    } catch { /* graceful */ }
  }, [simId])

  useEffect(() => { loadData() }, [loadData])

  /* Realtime subscriptions ------------------------------------------------ */
  useEffect(() => {
    if (!simId) return

    const simRunChannel = supabase
      .channel(`pub_sim:${simId}`)
      .on('postgres_changes', {
        event: 'UPDATE', schema: 'public', table: 'sim_runs',
        filter: `id=eq.${simId}`,
      }, (payload) => {
        const row = payload.new as Record<string, unknown>
        if (row) {
          setSimRun((prev) => prev ? { ...prev, ...row } as SimRun : prev)
          setSimState({
            status: (row.status as string) ?? 'setup',
            current_round: (row.current_round as number) ?? 0,
            current_phase: (row.current_phase as string) ?? 'pre',
            phase_started_at: (row.phase_started_at as string | null) ?? null,
            phase_duration_seconds: (row.phase_duration_seconds as number | null) ?? 3600,
            max_rounds: (row.max_rounds as number) ?? 8,
          })
        }
      })
      .subscribe()

    const eventsChannel = supabase
      .channel(`pub_events:${simId}`)
      .on('postgres_changes', {
        event: 'INSERT', schema: 'public', table: 'observatory_events',
        filter: `sim_run_id=eq.${simId}`,
      }, (payload) => {
        const evt = payload.new as PublicEvent
        if (evt) setEvents((prev) => [evt, ...prev].slice(0, 50))
      })
      .subscribe()

    const fallback = setInterval(loadData, 30000)

    return () => {
      supabase.removeChannel(simRunChannel)
      supabase.removeChannel(eventsChannel)
      clearInterval(fallback)
    }
  }, [simId, loadData])

  /* Timer countdown ------------------------------------------------------- */
  useEffect(() => {
    if (timerRef.current) clearInterval(timerRef.current)
    if (!simState?.phase_started_at || simState.status === 'paused') {
      setRemaining(null)
      return
    }
    const tick = () => {
      const now = Date.now()
      const started = new Date(simState.phase_started_at!).getTime()
      const elapsed = (now - started) / 1000
      setRemaining((simState.phase_duration_seconds ?? 3600) - elapsed)
    }
    tick()
    timerRef.current = setInterval(tick, 1000)
    return () => { if (timerRef.current) clearInterval(timerRef.current) }
  }, [simState?.phase_started_at, simState?.phase_duration_seconds, simState?.status])

  /* Derived --------------------------------------------------------------- */
  const currentRound = simState?.current_round ?? 0
  const currentPhase = simState?.current_phase ?? 'pre'
  const simDate = ROUND_TO_DATE[currentRound] ?? `R${currentRound}`
  const significantEvents = events.filter((e) => SIGNIFICANT_EVENTS.has(e.event_type))

  /* Render ---------------------------------------------------------------- */
  if (!simRun) {
    return (
      <div className="min-h-screen bg-[#0A0E1A] flex items-center justify-center">
        <p className="font-heading text-h2 text-text-secondary">Loading simulation...</p>
      </div>
    )
  }

  return (
    <div className="h-screen bg-[#0A0E1A] flex flex-col overflow-hidden">
      {/* ================================================================ */}
      {/*  HEADER                                                          */}
      {/* ================================================================ */}
      <header className="flex items-center justify-between px-6 py-3 border-b border-white/10">
        <div className="flex items-center gap-6">
          <span className="font-heading text-3xl text-white tracking-wide">
            R{currentRound}
          </span>
          <span className="font-body text-lg text-white/60 uppercase tracking-widest">
            {phaseLabel(currentPhase)}
          </span>
          {remaining !== null && (
            <span className={`font-data text-3xl ${
              remaining < 0 ? 'text-danger animate-pulse' : 'text-white'
            }`}>
              {formatTimer(remaining)}
            </span>
          )}
        </div>
        <div className="flex items-center gap-6">
          <span className="font-heading text-xl text-accent">
            {simDate}
          </span>
          <span className="font-body text-sm text-white/40">
            {simRun.name}
          </span>
        </div>
      </header>

      {/* ================================================================ */}
      {/*  MAIN AREA                                                       */}
      {/* ================================================================ */}
      <div className="flex-1 flex overflow-hidden">

        {/* ── MAP AREA (left, ~65%) ──────────────────────────────────── */}
        <div className="flex-[2] flex flex-col border-r border-white/10">
          {/* Map iframe */}
          <div className="flex-1 relative">
            <iframe
              src="/map/deployments.html"
              className="absolute inset-0 w-full h-full border-0"
              title="Global Map"
            />
          </div>

          {/* Columbia vs Cathay Power Balance */}
          <div className="px-6 py-3 border-t border-white/10">
            <div className="flex items-center gap-3 mb-1">
              <span className="font-body text-caption text-white/60 uppercase tracking-wider">
                Columbia vs Cathay — Power Balance
              </span>
            </div>
            <PowerBalanceBar simId={simId!} />
          </div>
        </div>

        {/* ── RIGHT PANEL (~35%) ─────────────────────────────────────── */}
        <div className="flex-[1] flex flex-col min-w-[300px]">

          {/* Doomsday Indices */}
          <div className="flex-1 px-5 py-4 space-y-4 overflow-hidden">
            <h3 className="font-heading text-sm text-white/40 uppercase tracking-widest mb-2">
              World Status
            </h3>

            <DoomsdayGauge
              label="Geopolitical Tension"
              value={indices.geopolitical_tension}
              prev={indices.prev_geopolitical_tension}
              max={10}
              dangerUp
              colorHigh="danger"
            />
            <DoomsdayGauge
              label="Economic Health"
              value={indices.economic_health}
              prev={indices.prev_economic_health}
              max={10}
              dangerUp={false}
              colorHigh="success"
            />
            <DoomsdayGauge
              label="Nuclear Danger"
              value={indices.nuclear_danger}
              prev={indices.prev_nuclear_danger}
              max={10}
              dangerUp
              colorHigh="danger"
            />
            <DoomsdayGauge
              label="AI Race"
              value={indices.ai_race}
              prev={indices.prev_ai_race}
              max={10}
              dangerUp
              colorHigh="warning"
            />
          </div>
        </div>
      </div>

      {/* ================================================================ */}
      {/*  NEWS TICKER (bottom)                                            */}
      {/* ================================================================ */}
      <footer className="border-t border-white/10 bg-[#0D1220] px-6 py-2 overflow-hidden">
        <div
          ref={tickerRef}
          className="flex items-center gap-8 animate-[scroll_60s_linear_infinite] whitespace-nowrap"
          style={{
            animationName: 'tickerScroll',
          }}
        >
          {significantEvents.length === 0 ? (
            <span className="font-body text-sm text-white/30">
              Awaiting events...
            </span>
          ) : (
            <>
              {significantEvents.map((evt) => (
                <span key={evt.id} className="font-body text-sm text-white/70 inline-flex items-center gap-2">
                  <span className={`w-1.5 h-1.5 rounded-full ${
                    evt.category === 'military' ? 'bg-danger' :
                    evt.category === 'economic' ? 'bg-accent' :
                    evt.category === 'diplomatic' ? 'bg-action' :
                    evt.category === 'political' ? 'bg-warning' :
                    'bg-white/30'
                  }`} />
                  {evt.summary}
                </span>
              ))}
              {/* Duplicate for seamless loop */}
              {significantEvents.map((evt) => (
                <span key={`dup-${evt.id}`} className="font-body text-sm text-white/70 inline-flex items-center gap-2">
                  <span className={`w-1.5 h-1.5 rounded-full ${
                    evt.category === 'military' ? 'bg-danger' :
                    evt.category === 'economic' ? 'bg-accent' :
                    evt.category === 'diplomatic' ? 'bg-action' :
                    evt.category === 'political' ? 'bg-warning' :
                    'bg-white/30'
                  }`} />
                  {evt.summary}
                </span>
              ))}
            </>
          )}
        </div>
      </footer>

      {/* Ticker animation */}
      <style>{`
        @keyframes tickerScroll {
          0% { transform: translateX(0); }
          100% { transform: translateX(-50%); }
        }
      `}</style>
    </div>
  )
}

/* -------------------------------------------------------------------------- */
/*  Sub-components                                                            */
/* -------------------------------------------------------------------------- */

/** Single doomsday gauge with bar, value, trend arrow. */
function DoomsdayGauge({
  label, value, prev, max, dangerUp, colorHigh,
}: {
  label: string
  value: number
  prev: number
  max: number
  dangerUp: boolean
  colorHigh: 'danger' | 'success' | 'warning' | 'accent'
}) {
  const pct = Math.min(100, (value / max) * 100)
  const arrow = trendArrow(value, prev)
  const trend = trendColor(value, prev, dangerUp)

  const barColor = colorHigh === 'danger' ? 'bg-danger'
    : colorHigh === 'success' ? 'bg-success'
    : colorHigh === 'warning' ? 'bg-warning'
    : 'bg-accent'

  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <span className="font-body text-xs text-white/50 uppercase tracking-wider">
          {label}
        </span>
        <div className="flex items-center gap-2">
          <span className={`font-data text-lg ${trend}`}>
            {arrow}
          </span>
          <span className="font-data text-xl text-white">
            {value}
          </span>
          <span className="font-data text-xs text-white/30">
            /{max}
          </span>
        </div>
      </div>
      <div className="w-full bg-white/5 rounded-full h-3">
        <div
          className={`h-3 rounded-full transition-all duration-1000 ${barColor}`}
          style={{ width: `${pct}%`, opacity: 0.8 }}
        />
      </div>
    </div>
  )
}

/** Columbia vs Cathay power balance bar. */
function PowerBalanceBar({ simId }: { simId: string }) {
  const [colPower, setColPower] = useState(55)
  const [catPower, setCatPower] = useState(45)

  useEffect(() => {
    if (!simId) return
    // Load GDP + military + tech for both countries
    supabase
      .from('countries')
      .select('id, gdp, mil_ground, mil_naval, mil_tactical_air, mil_strategic_missiles, mil_air_defense, nuclear_level, ai_level')
      .eq('sim_run_id', simId)
      .in('id', ['columbia', 'cathay'])
      .then(({ data }) => {
        if (!data || data.length < 2) return
        const col = data.find((c) => c.id === 'columbia')
        const cat = data.find((c) => c.id === 'cathay')
        if (!col || !cat) return

        const milScore = (c: typeof col) =>
          (c.mil_ground ?? 0) + (c.mil_naval ?? 0) * 2 + (c.mil_tactical_air ?? 0) * 1.5 +
          (c.mil_strategic_missiles ?? 0) * 3 + (c.mil_air_defense ?? 0)

        const power = (c: typeof col) =>
          (c.gdp ?? 0) * 0.4 + milScore(c) * 0.3 + (c.nuclear_level ?? 0) * 10 + (c.ai_level ?? 0) * 8

        const cp = power(col)
        const tp = power(cat)
        const total = cp + tp || 1
        setColPower(Math.round((cp / total) * 100))
        setCatPower(Math.round((tp / total) * 100))
      })
  }, [simId])

  return (
    <div className="flex items-center gap-3">
      <span className="font-data text-sm text-action w-20 text-right">
        Columbia {colPower}%
      </span>
      <div className="flex-1 flex h-4 rounded-full overflow-hidden bg-white/5">
        <div
          className="bg-action/70 transition-all duration-1000"
          style={{ width: `${colPower}%` }}
        />
        <div
          className="bg-danger/70 transition-all duration-1000"
          style={{ width: `${catPower}%` }}
        />
      </div>
      <span className="font-data text-sm text-danger w-20">
        {catPower}% Cathay
      </span>
    </div>
  )
}
