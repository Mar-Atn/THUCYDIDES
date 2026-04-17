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
    geopolitical_tension: 5, economic_health: 6, nuclear_danger: 4, ai_race: 4,
    prev_geopolitical_tension: 5, prev_economic_health: 6, prev_nuclear_danger: 4, prev_ai_race: 4,
  })
  const [colPower, setColPower] = useState(55)
  const [catPower, setCatPower] = useState(45)
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
          {currentPhase === 'B' && (
            <span className="font-body text-lg text-warning uppercase tracking-widest">
              PROCESSING
            </span>
          )}
          {simState?.status === 'paused' && (
            <span className="font-body text-lg text-text-secondary uppercase tracking-widest">
              PAUSED
            </span>
          )}
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

        {/* ── LEFT: MAP + COLUMBIA-CATHAY (~65%) ─────────────────────── */}
        <div className="flex-[2] flex flex-col border-r border-white/10">
          {/* Map iframe */}
          <div className="flex-1 relative">
            <iframe
              src="/map/deployments.html?display=clean"
              className="absolute inset-0 w-full h-full border-0"
              title="Global Map"
            />
          </div>

          {/* Columbia vs Cathay Power Balance (below map) */}
          <div className="px-6 py-2 border-t border-white/10">
            <PowerBalanceBar simId={simId!} />
          </div>
        </div>

        {/* ── RIGHT PANEL (~35%) ─────────────────────────────────────── */}
        <div className="flex-[1] flex flex-col min-w-[280px]">

          {/* Doomsday Indices */}
          <div className="px-5 py-4 space-y-3 border-b border-white/10">
            <h3 className="font-heading text-xs text-white/40 uppercase tracking-widest">
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
              label="Global Economic Health"
              value={indices.economic_health}
              prev={indices.prev_economic_health}
              max={10}
              dangerUp={false}
              colorHigh="success"
            />
            <DoomsdayGauge
              label="Doomsday Clock"
              value={indices.nuclear_danger}
              prev={indices.prev_nuclear_danger}
              max={10}
              dangerUp
              colorHigh="danger"
            />
            <DoomsdayGauge
              label="Distance to AGI"
              value={indices.ai_race}
              prev={indices.prev_ai_race}
              max={10}
              dangerUp
              colorHigh="warning"
            />
          </div>

          {/* Columbia vs Cathay Historical Power Graph */}
          <div className="px-5 py-4 border-b border-white/10">
            <h3 className="font-heading text-xs text-white/40 uppercase tracking-widest mb-2">
              Global Power Index
            </h3>
            <PowerTrendGraph colPower={colPower} catPower={catPower} />
          </div>

          {/* Empty space — future use */}
          <div className="flex-1" />
        </div>
      </div>

      {/* ================================================================ */}
      {/*  NEWS TICKER (bottom)                                            */}
      {/* ================================================================ */}
      <footer className="border-t border-white/10 bg-[#0D1220] overflow-hidden" style={{ height: '56px' }}>
        {significantEvents.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <span className="font-body text-sm text-white/30">Awaiting events...</span>
          </div>
        ) : (
          <>
            {/* Line 1 */}
            <div className="overflow-hidden whitespace-nowrap px-6 py-1">
              <div
                className="inline-flex items-center gap-8"
                style={{ animation: 'tickerScroll 80s linear infinite' }}
              >
                {significantEvents.filter((_, i) => i % 2 === 0).map((evt) => (
                  <span key={evt.id} className="font-body text-sm text-white/70 inline-flex items-center gap-2">
                    <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${
                      evt.category === 'military' ? 'bg-danger' :
                      evt.category === 'economic' ? 'bg-accent' :
                      evt.category === 'diplomatic' ? 'bg-action' :
                      evt.category === 'political' ? 'bg-warning' : 'bg-white/30'
                    }`} />
                    {evt.summary}
                  </span>
                ))}
                {significantEvents.filter((_, i) => i % 2 === 0).map((evt) => (
                  <span key={`d1-${evt.id}`} className="font-body text-sm text-white/70 inline-flex items-center gap-2">
                    <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${
                      evt.category === 'military' ? 'bg-danger' :
                      evt.category === 'economic' ? 'bg-accent' :
                      evt.category === 'diplomatic' ? 'bg-action' :
                      evt.category === 'political' ? 'bg-warning' : 'bg-white/30'
                    }`} />
                    {evt.summary}
                  </span>
                ))}
              </div>
            </div>
            {/* Line 2 */}
            <div className="overflow-hidden whitespace-nowrap px-6 py-1">
              <div
                className="inline-flex items-center gap-8"
                style={{ animation: 'tickerScroll 90s linear infinite reverse' }}
              >
                {significantEvents.filter((_, i) => i % 2 === 1).map((evt) => (
                  <span key={evt.id} className="font-body text-sm text-white/60 inline-flex items-center gap-2">
                    <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${
                      evt.category === 'military' ? 'bg-danger' :
                      evt.category === 'economic' ? 'bg-accent' :
                      evt.category === 'diplomatic' ? 'bg-action' :
                      evt.category === 'political' ? 'bg-warning' : 'bg-white/30'
                    }`} />
                    {evt.summary}
                  </span>
                ))}
                {significantEvents.filter((_, i) => i % 2 === 1).map((evt) => (
                  <span key={`d2-${evt.id}`} className="font-body text-sm text-white/60 inline-flex items-center gap-2">
                    <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${
                      evt.category === 'military' ? 'bg-danger' :
                      evt.category === 'economic' ? 'bg-accent' :
                      evt.category === 'diplomatic' ? 'bg-action' :
                      evt.category === 'political' ? 'bg-warning' : 'bg-white/30'
                    }`} />
                    {evt.summary}
                  </span>
                ))}
              </div>
            </div>
          </>
        )}
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

/** Doomsday gauge — analogue speedometer style with needle. */
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
  const pct = Math.min(1, value / max)
  const arrow = trendArrow(value, prev)
  const trend = trendColor(value, prev, dangerUp)

  // Needle angle: -120° (min) to +120° (max) — 240° arc
  const angle = -120 + pct * 240

  // Arc color gradient stops
  const arcColor = colorHigh === 'danger' ? '#EF4444'
    : colorHigh === 'success' ? '#22C55E'
    : colorHigh === 'warning' ? '#F59E0B'
    : '#3B82F6'

  return (
    <div className="flex items-center gap-3">
      {/* Speedometer SVG */}
      <svg viewBox="0 0 100 60" className="w-20 h-12 shrink-0">
        {/* Background arc */}
        <path
          d="M 10 55 A 40 40 0 0 1 90 55"
          fill="none"
          stroke="rgba(255,255,255,0.08)"
          strokeWidth="6"
          strokeLinecap="round"
        />
        {/* Colored arc (filled to current value) */}
        <path
          d="M 10 55 A 40 40 0 0 1 90 55"
          fill="none"
          stroke={arcColor}
          strokeWidth="6"
          strokeLinecap="round"
          strokeDasharray={`${pct * 126} 126`}
          opacity="0.8"
        />
        {/* Needle */}
        <line
          x1="50" y1="55"
          x2={50 + 30 * Math.cos((angle - 90) * Math.PI / 180)}
          y2={55 + 30 * Math.sin((angle - 90) * Math.PI / 180)}
          stroke="white"
          strokeWidth="2"
          strokeLinecap="round"
        />
        {/* Center dot */}
        <circle cx="50" cy="55" r="3" fill="white" opacity="0.8" />
        {/* Value text */}
        <text x="50" y="48" textAnchor="middle" fill="white" fontSize="14" fontFamily="var(--font-data, monospace)" fontWeight="bold">
          {value}
        </text>
      </svg>

      {/* Label + trend */}
      <div className="flex-1 min-w-0">
        <div className="font-body text-xs text-white/50 uppercase tracking-wider truncate">
          {label}
        </div>
        <div className="flex items-center gap-1 mt-0.5">
          <span className={`font-data text-sm ${trend}`}>
            {arrow} {prev !== value ? `from ${prev}` : 'stable'}
          </span>
        </div>
      </div>
    </div>
  )
}

/** Columbia vs Cathay power balance — live bar. */
function PowerBalanceBar({ simId }: { simId: string }) {
  const [col, setCol] = useState(55)
  const [cat, setCat] = useState(45)

  useEffect(() => {
    if (!simId) return
    supabase
      .from('countries')
      .select('id, gdp, mil_ground, mil_naval, mil_tactical_air, mil_strategic_missiles, mil_air_defense, nuclear_level, ai_level')
      .eq('sim_run_id', simId)
      .in('id', ['columbia', 'cathay'])
      .then(({ data }) => {
        if (!data || data.length < 2) return
        const colD = data.find((c) => c.id === 'columbia')
        const catD = data.find((c) => c.id === 'cathay')
        if (!colD || !catD) return

        const milScore = (c: typeof colD) =>
          (c.mil_ground ?? 0) + (c.mil_naval ?? 0) * 2 + (c.mil_tactical_air ?? 0) * 1.5 +
          (c.mil_strategic_missiles ?? 0) * 3 + (c.mil_air_defense ?? 0)

        const power = (c: typeof colD) =>
          (c.gdp ?? 0) * 0.4 + milScore(c) * 0.3 + (c.nuclear_level ?? 0) * 10 + (c.ai_level ?? 0) * 8

        const cp = power(colD)
        const tp = power(catD)
        const total = cp + tp || 1
        setCol(Math.round((cp / total) * 100))
        setCat(Math.round((tp / total) * 100))
      })
  }, [simId])

  return (
    <div className="flex items-center gap-3">
      <span className="font-data text-xs text-action w-24 text-right">
        Columbia {col}%
      </span>
      <div className="flex-1 flex h-4 rounded-full overflow-hidden bg-white/5">
        <div className="bg-action/70 transition-all duration-1000" style={{ width: `${col}%` }} />
        <div className="bg-danger/70 transition-all duration-1000" style={{ width: `${cat}%` }} />
      </div>
      <span className="font-data text-xs text-danger w-24">
        {cat}% Cathay
      </span>
    </div>
  )
}

/** Columbia vs Cathay historical power trend — two lines converging. */
function PowerTrendGraph({ colPower, catPower }: { colPower: number; catPower: number }) {
  // Expert-estimated Global Power Index (arbitrary units, not %)
  // Columbia: growing slowly. Cathay: growing fast, closing the gap.
  // 2006-2026 historical, then SIM rounds extend the trend.
  const labels = ['2006','','2010','','2014','','2018','','2022','','2026','SIM']
  // Columbia: dominant but plateauing (100 → ~120)
  const colData = [100, 104, 108, 110, 112, 114, 115, 116, 117, 118, 119, 115 + (colPower / 10)]
  // Cathay: rapid catch-up (40 → ~95)
  const catData = [40,  46,  52,  58,  65,  72,  78,  83,  87,  91,  95,  90 + (catPower / 10)]

  const maxVal = Math.max(...colData, ...catData) * 1.1
  const w = 240
  const h = 80

  const toPoints = (data: number[]) =>
    data.map((v, i) => `${i * (w / (data.length - 1))},${h - (v / maxVal) * h}`).join(' ')

  return (
    <div>
      <svg viewBox={`0 0 ${w} ${h + 16}`} className="w-full h-24">
        {/* Grid lines */}
        {[0.25, 0.5, 0.75].map((f) => (
          <line key={f} x1="0" y1={h * f} x2={w} y2={h * f} stroke="white" strokeWidth="0.3" opacity="0.1" />
        ))}

        {/* Columbia line (blue, thicker) */}
        <polyline fill="none" stroke="#3B82F6" strokeWidth="2.5" opacity="0.8" points={toPoints(colData)} />
        {/* Cathay line (red, thicker) */}
        <polyline fill="none" stroke="#EF4444" strokeWidth="2.5" opacity="0.8" points={toPoints(catData)} />

        {/* SIM boundary line */}
        <line x1={w * (10/11)} y1="0" x2={w * (10/11)} y2={h} stroke="white" strokeWidth="0.5" opacity="0.3" strokeDasharray="3,3" />

        {/* Labels */}
        <text x="2" y={h - (colData[0] / maxVal) * h - 4} fill="#3B82F6" fontSize="8" opacity="0.7">Columbia</text>
        <text x="2" y={h - (catData[0] / maxVal) * h + 10} fill="#EF4444" fontSize="8" opacity="0.7">Cathay</text>

        {/* End values */}
        <circle cx={w} cy={h - (colData[colData.length-1] / maxVal) * h} r="3" fill="#3B82F6" opacity="0.9" />
        <circle cx={w} cy={h - (catData[catData.length-1] / maxVal) * h} r="3" fill="#EF4444" opacity="0.9" />

        {/* Year labels at bottom */}
        {labels.map((l, i) => l ? (
          <text key={i} x={i * (w / (labels.length - 1))} y={h + 12} fill="white" fontSize="7" opacity="0.3" textAnchor="middle">
            {l}
          </text>
        ) : null)}
      </svg>
    </div>
  )
}
