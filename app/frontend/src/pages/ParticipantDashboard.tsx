/**
 * Participant Dashboard — what human players see during the simulation.
 * Route: /play/:simId
 *
 * Tabs: Actions | Strictly Confidential | Country | World | Global Map
 * Persistent: Header (role + round + timer), Navigator button, Moderator broadcast
 *
 * M6 Sprint 6.1: Shell, tabs, header, data loading
 */

import { useEffect, useState, useCallback, useRef, useMemo } from 'react'
import { useParams } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { supabase } from '@/lib/supabase'
import { channelManager, type RealtimeListener } from '@/lib/channelManager'
import { submitAction, getToken, type SimRun } from '@/lib/queries'
import { requestQueue } from '@/lib/requestQueue'
import { ArtefactRenderer } from '@/components/ArtefactRenderer'
import { useRealtimeRow, useRealtimeTable } from '@/hooks/useRealtimeTable'
import {
  ActionForm, TransactionReview, ArrestedBanner, UnitIcon,
} from '@/components/participant/ActionForms'
import { MeetingChat } from '@/components/participant/MeetingChat'
import { getActiveMeetings, endMeeting, type MeetingData } from '@/lib/queries'

/* ── Hex → Country lookup (canonical from map_config.py) ──────────────── */
const HEX_OWNERS: Record<string, string> = {
  '2,10':'freeland','2,11':'sarmatia','2,12':'sarmatia','2,16':'sarmatia',
  '3,3':'columbia','3,6':'thule','3,8':'albion','3,10':'freeland',
  '3,11':'ruthenia','3,12':'sarmatia','3,13':'sarmatia','3,14':'sarmatia',
  '3,15':'sarmatia','3,16':'sarmatia','3,18':'choson',
  '4,2':'columbia','4,3':'columbia','4,7':'albion','4,9':'teutonia',
  '4,10':'teutonia','4,11':'ruthenia','4,12':'sarmatia','4,13':'sarmatia',
  '4,14':'sarmatia','4,16':'sarmatia','4,17':'hanguk','4,19':'yamato',
  '5,3':'columbia','5,4':'columbia','5,5':'columbia','5,9':'gallia',
  '5,10':'gallia','5,11':'phrygia','5,14':'sogdiana','5,15':'cathay',
  '5,16':'cathay','5,17':'cathay','5,19':'yamato',
  '6,3':'columbia','6,4':'columbia','6,8':'ponte','6,10':'levantia',
  '6,11':'phrygia','6,12':'persia','6,13':'sogdiana','6,14':'sogdiana',
  '6,15':'cathay','6,16':'cathay',
  '7,4':'columbia','7,9':'ponte','7,11':'solaria','7,13':'persia',
  '7,14':'bharata','7,15':'bharata','7,16':'cathay','7,18':'formosa',
  '8,10':'solaria','8,11':'mirage','8,13':'persia','8,14':'bharata',
  '8,15':'bharata',
  '9,5':'caribe','9,10':'horn','9,15':'bharata',
}
function hexCountryName(row: number, col: number): string {
  return (HEX_OWNERS[`${row},${col}`] || 'sea').toUpperCase()
}

/* ── Types ─────────────────────────────────────────────────────────────── */

interface RoleData {
  id: string; character_name: string; country_code: string; position_type: string; positions?: string[]; status?: string
  title: string; public_bio: string; confidential_brief: string | null
  objectives: string[]; powers: string[]
}

interface CountryData {
  id: string; sim_name: string; color_ui: string | null
  gdp: number; stability: number; inflation: number; treasury: number
  mil_ground: number; mil_naval: number; mil_tactical_air: number
  mil_strategic_missiles: number; mil_air_defense: number
  nuclear_level: number; nuclear_confirmed: boolean
  ai_level: number; debt_burden: number
}

interface Artefact {
  id: string; role_id: string; artefact_type: string; title: string
  subtitle: string | null; classification: string; from_entity: string | null
  date_label: string | null; content_html: string | null
  round_delivered: number; is_read: boolean
}

interface SimState {
  status: string; current_round: number; current_phase: string
  phase_started_at: string | null; phase_duration_seconds: number | null
}

type TabId = 'actions' | 'confidential' | 'country' | 'world' | 'map'

/* ── Helpers ───────────────────────────────────────────────────────────── */

const POS: Record<string, string> = {
  head_of_state: 'Head of State', military_chief: 'Military Chief',
  economy_officer: 'Economy Officer', diplomat: 'Diplomat',
  security: 'Security', opposition: 'Opposition',
  // New canonical position names (from positions[] array)
  military: 'Military', economy: 'Economy',
}
function displayPositions(role: { positions?: string[]; position_type: string }): string {
  const pos = role.positions
  // If positions array exists (even empty), it's the source of truth
  if (Array.isArray(pos)) {
    if (pos.length > 0) return pos.map(p => POS[p] ?? p).join(' + ')
    return 'Citizen'
  }
  // Fallback to legacy position_type only if positions not set
  return POS[role.position_type] ?? role.position_type ?? 'Citizen'
}

const RD: Record<number, string> = {
  0:'Pre-Sim',1:'H2 2026',2:'H1 2027',3:'H2 2027',4:'H1 2028',5:'H2 2028',6:'H1 2029',7:'H2 2029',8:'H1 2030',
}

function fmtTimer(s: number) { if (s<0) return 'OVERTIME'; const m=Math.floor(s/60),ss=Math.floor(s%60); return `${String(m).padStart(2,'0')}:${String(ss).padStart(2,'0')}` }

/* ── Action Catalog ────────────────────────────────────────────────────── */

// Actions shown conditionally: move_units only during inter_round phase
const PHASE_RESTRICTED: Record<string, string> = { move_units: 'inter_round' }

const CATS: { key: string; label: string; actions: { id: string; label: string }[] }[] = [
  { key:'general', label:'General', actions:[
    {id:'public_statement',label:'Public Statement'},{id:'invite_to_meet',label:'Set Meetings'},
  ]},
  { key:'economic', label:'Economic', actions:[
    {id:'set_budget',label:'Set Budget'},{id:'set_tariffs',label:'Set Tariffs'},
    {id:'set_sanctions',label:'Set Sanctions'},{id:'set_opec',label:'Set Cartel Production'},
  ]},
  { key:'intl', label:'International Affairs & Trade', actions:[
    {id:'propose_transaction',label:'Propose Transaction'},
    {id:'propose_agreement',label:'Propose Agreement'},
    {id:'basing_rights',label:'Grant / Revoke Basing Rights'},
    {id:'declare_war',label:'Declare War'},
  ]},
  { key:'military', label:'Military', actions:[
    {id:'attack',label:'Attack'},
    {id:'naval_blockade',label:'Blockade'},{id:'move_units',label:'Move Units (inter-round)'},
    {id:'martial_law',label:'Martial Law'},{id:'nuclear_test',label:'Nuclear Test'},
    {id:'nuclear_launch_initiate',label:'Nuclear Launch'},
  ]},
  { key:'political', label:'Political', actions:[
    {id:'reassign_types',label:'Reassign Powers'},{id:'arrest',label:'Arrest'},{id:'change_leader',label:'Change Leader'},
    {id:'self_nominate',label:'Self-Nominate'},{id:'cast_vote',label:'Cast Vote'},
  ]},
  { key:'covert', label:'Secret Operations', actions:[
    {id:'intelligence',label:'Intelligence'},{id:'covert_operation',label:'Covert Operation'},{id:'assassination',label:'Assassination'},
  ]},
]

/* ── Main Component ────────────────────────────────────────────────────── */

export function ParticipantDashboard() {
  const { simId } = useParams<{ simId: string }>()
  const { user, profile } = useAuth()

  // Clear stale request queue on mount (prevents Loading... stuck state after navigation)
  useEffect(() => { requestQueue.reset() }, [])

  // Proxy mode: ?role=sabre allows moderator to view as a specific role
  const urlParams = new URLSearchParams(window.location.search)
  const proxyRoleId = urlParams.get('role')
  const isProxyMode = !!proxyRoleId

  const [myRole, setMyRole] = useState<RoleData | null>(null)
  const [myCountry, setMyCountry] = useState<CountryData | null>(null)
  const [artefacts, setArtefacts] = useState<Artefact[]>([])
  const [tab, setTab] = useState<TabId>('actions')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [remaining, setRemaining] = useState<number | null>(null)
  const [broadcast, setBroadcast] = useState<string | null>(null)
  const [roleActions, setRoleActions] = useState<string[]>([])
  const [dataVersion, setDataVersion] = useState(0) // increments on every loadData — children use as refresh trigger
  const [objectives, setObjectives] = useState<string[]>([])
  const [myRelationships, setMyRelationships] = useState<{to_country_code:string;relationship:string;status:string}[]>([])
  const [myOrgMemberships, setMyOrgMemberships] = useState<{org_id:string;role_in_org:string;has_veto:boolean}[]>([])
  const [personalRels, setPersonalRels] = useState<{other_role:string;type:string;notes:string}[]>([])
  const [activeAction, setActiveAction] = useState<string|null>(null)
  const [activeChatMeetingId, setActiveChatMeetingId] = useState<string|null>(null)
  const [mySanctions, setMySanctions] = useState<{imposer:string;target:string;level:number}[]>([])
  const [myTariffs, setMyTariffs] = useState<{imposer:string;target:string;level:number}[]>([])
  const [fullCountry, setFullCountry] = useState<Record<string,unknown>|null>(null)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const prevRoundRef = useRef<number | null>(null)
  const [nuclearBannerDismissed, setNuclearBannerDismissed] = useState(false)
  const nuclearBannerTimerRef = useRef<ReturnType<typeof setTimeout>|null>(null)

  /* Realtime hook for sim_runs — replaces manual channel + polling -------- */
  const { data: simRun } = useRealtimeRow<SimRun>('sim_runs', simId)

  /* Realtime hook for nuclear_actions — global flight banner ------------- */
  const { data: globalNuclearActions } = useRealtimeTable<Record<string, unknown>>(
    'nuclear_actions', simId,
  )

  // Ticking countdown for nuclear flight banner
  const activeFlightAction = (globalNuclearActions as unknown as {
    id:string; status:string; country_code:string; payload:Record<string,unknown>;
    timer_started_at:string|null; timer_duration_sec:number|null;
  }[])?.find(a => a.status === 'awaiting_interception') ?? null
  const [nuclearCountdown, setNuclearCountdown] = useState<number|null>(null)
  useEffect(() => {
    if (!activeFlightAction) { setNuclearCountdown(null); return }
    const started = new Date(activeFlightAction.timer_started_at!).getTime()
    const dur = activeFlightAction.timer_duration_sec ?? 600
    const tick = () => setNuclearCountdown(Math.max(0, dur - (Date.now() - started) / 1000))
    tick()
    const iv = setInterval(tick, 1000)
    return () => clearInterval(iv)
  }, [activeFlightAction?.id, activeFlightAction?.status])

  /* Auto-open chat when a meeting is created for my outgoing invitation --- */
  useEffect(() => {
    if (!simId || !myRole) return
    const ch = supabase
      .channel(`meeting-autoopen:${myRole.id}`)
      .on(
        'postgres_changes',
        { event: 'INSERT', schema: 'public', table: 'meetings' },
        (payload) => {
          const row = payload.new as Record<string, unknown>
          if (row.sim_run_id !== simId) return
          // Auto-open if I'm a participant and not already in a chat
          const isMyMeeting = row.participant_a_role_id === myRole.id || row.participant_b_role_id === myRole.id
          if (isMyMeeting && !activeChatMeetingId) {
            setActiveChatMeetingId(row.id as string)
          }
        },
      )
      .subscribe()
    return () => { supabase.removeChannel(ch) }
  }, [simId, myRole?.id]) // eslint-disable-line react-hooks/exhaustive-deps

  /* Derive simState from the realtime sim_runs row ----------------------- */
  const simState: SimState | null = simRun ? {
    status: simRun.status,
    current_round: simRun.current_round,
    current_phase: simRun.current_phase,
    phase_started_at: simRun.started_at,
    phase_duration_seconds: (simRun.schedule as Record<string, number>)?.phase_a_minutes
      ? (simRun.schedule as Record<string, number>).phase_a_minutes * 60
      : 3600,
  } : null

  /* loadData — fetches role, country, artefacts, etc. Called once on mount
     and again when the round changes (not on every sim_runs update). ------ */
  const loadData = useCallback(async () => {
    if (!simId || !user) return
    try {
      // Load role: proxy mode uses role_id, normal mode uses user_id
      const roleQuery = supabase.from('roles')
        .select('id,character_name,country_code,position_type,positions,title,public_bio,confidential_brief,objectives,powers,status,status_detail')
        .eq('sim_run_id',simId)
      const { data: roles } = proxyRoleId
        ? await roleQuery.eq('id', proxyRoleId).limit(1)
        : await roleQuery.eq('user_id', user.id).limit(1)
      if (roles?.[0]) {
        const role = roles[0] as RoleData; setMyRole(role)
        setObjectives(Array.isArray(role.objectives) ? role.objectives as string[] : [])

        // Batch all independent queries into one Promise.all
        // This reduces sequential wait from 13 round-trips to 1
        const [countryRes, artsRes, raRes, relsRes, memsRes, prARes, prBRes, srRes, trRes] = await Promise.all([
          supabase.from('countries').select('*')
            .eq('sim_run_id',simId).eq('id',role.country_code).limit(1),
          supabase.from('artefacts').select('*')
            .eq('sim_run_id',simId).eq('role_id',role.id).order('round_delivered'),
          supabase.from('role_actions').select('action_id')
            .eq('sim_run_id',simId).eq('role_id',role.id),
          supabase.from('relationships')
            .select('to_country_code,relationship,status')
            .eq('sim_run_id',simId).eq('from_country_code',role.country_code),
          supabase.from('org_memberships')
            .select('org_id,role_in_org,has_veto')
            .eq('sim_run_id',simId).eq('country_code',role.country_code),
          supabase.from('role_relationships')
            .select('role_a_id,role_b_id,relationship_type,notes')
            .eq('sim_run_id',simId).eq('role_a_id',role.id),
          supabase.from('role_relationships')
            .select('role_a_id,role_b_id,relationship_type,notes')
            .eq('sim_run_id',simId).eq('role_b_id',role.id),
          supabase.from('sanctions')
            .select('imposer_country_code,target_country_code,level')
            .eq('sim_run_id',simId).or(`target_country_code.eq.${role.country_code},imposer_country_code.eq.${role.country_code}`),
          supabase.from('tariffs')
            .select('imposer_country_code,target_country_code,level')
            .eq('sim_run_id',simId).or(`target_country_code.eq.${role.country_code},imposer_country_code.eq.${role.country_code}`),
        ])

        if (countryRes.data?.[0]) {
          setMyCountry(countryRes.data[0] as CountryData)
          setFullCountry(countryRes.data[0])
        }
        setArtefacts((artsRes.data??[]) as Artefact[])
        setRoleActions((raRes.data??[]).map((r:{action_id:string})=>r.action_id))
        setMyRelationships((relsRes.data??[]) as typeof myRelationships)
        setMyOrgMemberships((memsRes.data??[]) as typeof myOrgMemberships)
        const pRels = [
          ...((prARes.data??[]).map((r:{role_a_id:string;role_b_id:string;relationship_type:string;notes:string})=>({other_role:r.role_b_id,type:r.relationship_type,notes:r.notes||''}))),
          ...((prBRes.data??[]).map((r:{role_a_id:string;role_b_id:string;relationship_type:string;notes:string})=>({other_role:r.role_a_id,type:r.relationship_type,notes:r.notes||''}))),
        ]
        setPersonalRels(pRels)
        const sanctions = (srRes.data??[]).map((s:{imposer_country_code:string;target_country_code:string;level:number})=>({imposer:s.imposer_country_code,target:s.target_country_code,level:s.level}))
        setMySanctions(sanctions)
        const tariffs = (trRes.data??[]).map((t:{imposer_country_code:string;target_country_code:string;level:number})=>({imposer:t.imposer_country_code,target:t.target_country_code,level:t.level}))
        setMyTariffs(tariffs)

      } else { setTab('world') }
      setError(null)
    } catch(e) { setError(e instanceof Error?e.message:'Failed') }
    finally { setLoading(false); setDataVersion(v => v + 1) }
  }, [simId, user])

  // Initial data load — once on mount
  useEffect(() => { loadData() }, [loadData])

  // Realtime: auto-reload when moderator assigns a role to this user
  useEffect(() => {
    if (!user?.id || !simId || isProxyMode) return
    const ch = supabase
      .channel(`role-assign-${user.id}-${simId}`)
      .on('postgres_changes', {
        event: 'UPDATE', schema: 'public', table: 'roles',
        filter: `sim_run_id=eq.${simId}`,
      }, (payload) => {
        const newRow = payload.new as Record<string, unknown>
        if (newRow.user_id === user.id && !myRole) {
          // Role just assigned to me — reload everything
          loadData()
        }
      })
      .subscribe()
    return () => { supabase.removeChannel(ch) }
  }, [user?.id, simId, isProxyMode, myRole, loadData])

  // Reload data when round changes (new round means new country stats, artefacts, etc.)
  useEffect(() => {
    if (simRun === null) return
    const newRound = simRun.current_round
    if (prevRoundRef.current !== null && prevRoundRef.current !== newRound) {
      loadData()
    }
    prevRoundRef.current = newRound
  }, [simRun?.current_round, loadData])

  /* Realtime: detect role status changes (arrest/release) --------------- */
  useEffect(() => {
    if (!myRole || !simId) return
    const listener: RealtimeListener = (payload) => {
      const newStatus = (payload.new as Record<string, unknown>)?.status as string
      if (newStatus && newStatus !== myRole.status) {
        setMyRole(prev => prev ? { ...prev, status: newStatus } : prev)
      }
    }
    const key = channelManager.subscribeRow('roles', myRole.id, listener)
    return () => { channelManager.unsubscribe(key, listener) }
  }, [myRole?.id, myRole?.status, simId])

  /* Timer countdown ------------------------------------------------------- */
  useEffect(() => {
    if(timerRef.current)clearInterval(timerRef.current)
    if(!simState?.phase_started_at||simState.status==='paused'){setRemaining(null);return}
    const tick=()=>{const e=(Date.now()-new Date(simState.phase_started_at!).getTime())/1000;setRemaining((simState.phase_duration_seconds??3600)-e)}
    tick();timerRef.current=setInterval(tick,1000)
    return()=>{if(timerRef.current)clearInterval(timerRef.current)}
  }, [simState?.phase_started_at,simState?.phase_duration_seconds,simState?.status])

  const round = simState?.current_round ?? 0
  const color = myCountry?.color_ui ?? '#4A5568'
  const hasRole = !!myRole
  const unread = artefacts.filter(a=>!a.is_read).length

  const tabs:{id:TabId;label:string;badge?:number;off?:boolean}[] = [
    {id:'actions',label:'Actions'},
    {id:'confidential',label:'Confidential',badge:unread||undefined},
    {id:'country',label:'Country'},
    {id:'world',label:'World'},
    {id:'map',label:'Map'},
  ]

  if (loading) return <div className="min-h-screen bg-base flex items-center justify-center"><div className="w-8 h-8 border-2 border-action border-t-transparent rounded-full animate-spin"/></div>
  if (error||!simRun) return <div className="min-h-screen bg-base flex items-center justify-center"><div className="bg-card border border-danger/30 rounded-lg p-8"><p className="font-body text-body text-danger">{error??'Not found'}</p></div></div>

  return (
    <div className="min-h-screen bg-base flex flex-col">
      {/* HEADER */}
      <header className="sticky top-0 z-30 bg-card border-b-2 px-6 py-3" style={{borderBottomColor:color}}>
        <div className="flex items-center justify-between max-w-7xl mx-auto">
          <div className="flex items-center gap-4">
            {hasRole ? (<>
              <div className="w-10 h-10 rounded-full flex items-center justify-center font-heading text-lg text-white" style={{backgroundColor:color}}>{myRole!.character_name[0]}</div>
              <div>
                <div className="font-heading text-h3 text-text-primary">{myRole!.character_name}</div>
                <div className="font-body text-caption text-text-secondary">{myRole!.title} · {myCountry?.sim_name??myRole!.country_code}</div>
              </div>
              <span className="font-body text-caption font-medium px-2 py-0.5 rounded" style={{backgroundColor:`${color}15`,color}}>{displayPositions(myRole!)}</span>
            </>) : (<div>
              <div className="font-heading text-h3 text-text-primary">{profile?.display_name??'Participant'}</div>
              <div className="font-body text-caption text-text-secondary">Awaiting role assignment</div>
            </div>)}
          </div>
          <div className="flex items-center gap-4">
            <div className="text-right">
              <div className="font-data text-data-lg text-text-primary">R{round}</div>
              <div className="font-body text-caption text-text-secondary">{RD[round]??''}</div>
            </div>
            {remaining!==null&&<span className={`font-data text-data-lg ${remaining<0?'text-danger animate-pulse':'text-text-primary'}`}>{fmtTimer(remaining)}</span>}
            {simState?.status==='paused'&&<span className="font-body text-caption text-warning bg-warning/10 px-2 py-0.5 rounded">PAUSED</span>}
          </div>
        </div>
      </header>

      {/* Proxy mode banner */}
      {isProxyMode&&<div className="bg-danger/10 border-b border-danger/30 px-6 py-2">
        <div className="max-w-7xl mx-auto flex items-center gap-3">
          <span className="font-body text-caption font-bold text-danger uppercase tracking-wider">Moderator View</span>
          <span className="font-body text-body-sm text-text-primary">
            Viewing as {myRole?.character_name ?? proxyRoleId} — actions will be attributed to this role
          </span>
          <button onClick={()=>window.close()} className="ml-auto font-body text-caption text-danger hover:underline">Close</button>
        </div>
      </div>}

      {broadcast&&<div className="bg-warning/10 border-b border-warning/30 px-6 py-2"><div className="max-w-7xl mx-auto flex items-center gap-3">
        <span className="font-body text-caption font-bold text-warning uppercase">Broadcast</span>
        <span className="font-body text-body-sm text-text-primary flex-1">{broadcast}</span>
        <button onClick={()=>setBroadcast(null)} className="text-text-secondary hover:text-text-primary">{'\u2715'}</button>
      </div></div>}

      {/* Arrested banner — blocks all actions */}
      {myRole?.status === 'arrested' && <ArrestedBanner simId={simId!} roleId={myRole.id} round={round} />}

      {/* Killed banner */}
      {myRole?.status === 'killed' && (
        <div className="bg-danger/10 border-b-2 border-danger/40 px-6 py-4">
          <div className="max-w-7xl mx-auto">
            <p className="font-heading text-h3 text-danger">You Have Been Killed</p>
            <p className="font-body text-body-sm text-text-primary">
              Your character has been assassinated. You can no longer take any actions in this simulation.
            </p>
          </div>
        </div>
      )}

      {/* Nuclear Flight Banner — shown to ALL participants during Phase 3 */}
      {(() => {
        const resolvedAction = !activeFlightAction && !nuclearBannerDismissed && (globalNuclearActions as unknown as {
          id:string; status:string; country_code:string; resolved_at:string|null;
        }[])?.find(a => {
          if (a.status !== 'resolved') return false
          if (!a.resolved_at) return false
          const resolvedAt = new Date(a.resolved_at).getTime()
          return (Date.now() - resolvedAt) < 30000 // Show for 30s after resolution
        })

        if (activeFlightAction && nuclearCountdown !== null) {
          const missiles = ((activeFlightAction.payload?.changes as Record<string,unknown>)?.missiles as unknown[]) ?? []
          const mm = String(Math.floor(nuclearCountdown / 60)).padStart(2, '0')
          const ss = String(Math.floor(nuclearCountdown % 60)).padStart(2, '0')

          return (
            <div style={{
              width:'100%',backgroundColor:'#991B1B',padding:'0.75rem 1.5rem',
              display:'flex',alignItems:'center',justifyContent:'center',gap:'1.5rem',
              animation:'nuclearBannerFlash 2s ease-in-out infinite',zIndex:40,
            }}>
              <span style={{
                fontFamily:'"JetBrains Mono",monospace',fontSize:'1.1rem',fontWeight:700,
                color:'#FFFFFF',letterSpacing:'0.1em',textTransform:'uppercase',
              }}>
                {'\u26A0'} BALLISTIC MISSILE LAUNCH DETECTED {'\u2014'} {activeFlightAction.country_code.toUpperCase()}
              </span>
              <span style={{
                fontFamily:'"JetBrains Mono",monospace',fontSize:'1.1rem',fontWeight:700,
                color:'#FFFFFF',letterSpacing:'0.1em',
              }}>
                {missiles.length} MISSILE{missiles.length > 1 ? 'S' : ''} INBOUND {'\u2014'} Impact in {mm}:{ss}
              </span>
            </div>
          )
        }

        if (resolvedAction) {
          // Auto-dismiss after 30s
          if (!nuclearBannerTimerRef.current) {
            nuclearBannerTimerRef.current = setTimeout(() => {
              setNuclearBannerDismissed(true)
              nuclearBannerTimerRef.current = null
            }, 30000)
          }
          return (
            <div style={{
              width:'100%',backgroundColor:'#1E3A5F',padding:'0.75rem 1.5rem',
              display:'flex',alignItems:'center',justifyContent:'center',gap:'1rem',
              zIndex:40,
            }}>
              <span style={{
                fontFamily:'"JetBrains Mono",monospace',fontSize:'1rem',fontWeight:700,
                color:'#FFFFFF',letterSpacing:'0.1em',textTransform:'uppercase',
              }}>
                NUCLEAR STRIKE RESOLVED
              </span>
            </div>
          )
        }
        return null
      })()}
      <style>{`
        @keyframes nuclearBannerFlash {
          0%, 100% { background-color: #991B1B; }
          50% { background-color: #DC2626; }
        }
      `}</style>

      {/* TABS */}
      <nav className="bg-card border-b border-border px-6">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex">
            {tabs.map(t=>(
              <button key={t.id} onClick={()=>{if(!t.off){setTab(t.id);setActiveAction(null)}}} disabled={t.off}
                className={`relative px-5 py-3 font-body text-body-sm font-medium transition-colors ${tab===t.id?'text-text-primary':t.off?'text-text-secondary/30 cursor-not-allowed':'text-text-secondary hover:text-text-primary'}`}>
                {t.label}
                {t.badge?<span className="absolute -top-0.5 -right-0.5 w-4 h-4 bg-danger text-white text-[10px] font-bold rounded-full flex items-center justify-center">{t.badge}</span>:null}
                {tab===t.id&&<div className="absolute bottom-0 left-0 right-0 h-0.5" style={{backgroundColor:color}}/>}
              </button>
            ))}
          </div>
          <div className="flex items-center gap-2">
            <button className="font-body text-caption text-action hover:underline px-3 py-2">Rules</button>
            <button className="flex items-center gap-1.5 bg-action/10 text-action font-body text-caption font-medium px-3 py-1.5 rounded-full hover:bg-action/20 transition-colors">
              <span className="w-2 h-2 bg-action rounded-full"/>Navigator
            </button>
          </div>
        </div>
      </nav>

      {/* CONTENT */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-6 py-6">
        {/* Unassigned state — role not yet assigned by moderator */}
        {!myRole && (tab === 'actions' || tab === 'confidential' || tab === 'country') && !loading && (
          <div className="bg-card border border-border rounded-lg p-8 text-center">
            <h3 className="font-heading text-h3 text-text-primary mb-3">Awaiting Role Assignment</h3>
            <p className="font-body text-body-sm text-text-secondary mb-2">
              The moderator will assign you a role before the simulation starts.
            </p>
            <p className="font-body text-caption text-text-secondary">
              Once assigned, this tab will show your {tab === 'actions' ? 'available actions' : tab === 'confidential' ? 'confidential briefing and intelligence' : 'country data and statistics'}.
            </p>
            <p className="font-body text-caption text-action mt-4">
              This page updates automatically — no need to refresh.
            </p>
          </div>
        )}
        {tab==='actions'&&myRole&&(myRole.status==='arrested'||myRole.status==='killed')&&(
          <div className="bg-danger/5 border border-danger/20 rounded-lg p-6 text-center">
            <h3 className="font-heading text-h3 text-danger mb-2">{myRole.status === 'killed' ? 'Eliminated' : 'Arrested'}</h3>
            <p className="font-body text-body-sm text-text-secondary">
              {myRole.status === 'killed'
                ? 'Your character has been assassinated. No actions are available.'
                : 'You cannot take any actions while under arrest. You will be released at the end of this round.'}
            </p>
          </div>
        )}
        {tab==='actions'&&myRole&&myRole.status!=='arrested'&&myRole.status!=='killed'&&(
          activeAction
            ? <ActionForm
                actionType={activeAction}
                roleId={myRole.id}
                roleName={myRole.character_name}
                countryId={myRole.country_code}
                simId={simId!}
                onClose={()=>setActiveAction(null)}
                onSubmitted={()=>{setActiveAction(null); loadData()}}
              />
            : <TabActions roleActions={roleActions} currentPhase={simState?.current_phase??'pre'} onSelectAction={setActiveAction}
                simId={simId!} countryId={myRole.country_code} roleId={myRole.id} dataVersion={dataVersion}
                nuclearActionsData={globalNuclearActions}
                parentOrgIds={new Set(myOrgMemberships.map(m=>m.org_id))}
                parentSimRun={simRun}
                onOpenChat={setActiveChatMeetingId}/>
        )}
        {tab==='confidential'&&myRole&&<TabConf role={myRole} artefacts={artefacts} objectives={objectives} personalRels={personalRels} orgMemberships={myOrgMemberships} onRead={id=>{
          supabase.from('artefacts').update({is_read:true}).eq('id',id).then(()=>{
            setArtefacts(p=>p.map(a=>a.id===id?{...a,is_read:true}:a))
          })
        }}/>}
        {tab==='country'&&myCountry&&<TabCountry country={myCountry} fullCountry={fullCountry} sanctions={mySanctions} tariffs={myTariffs} relationships={myRelationships} orgMemberships={myOrgMemberships} simId={simId!}/>}
        {tab==='world'&&<TabWorld simId={simId!} round={round}/>}
        {tab==='map'&&<div className="relative" style={{height:'calc(100vh - 180px)'}}>
          <iframe src={`/map/deployments.html?display=clean&sim_run_id=${simId}`} className="absolute inset-0 w-full h-full border-0 rounded-lg" title="Map"/>
        </div>}
      </main>

      {/* Meeting Chat overlay */}
      {activeChatMeetingId && myRole && (
        <MeetingChat
          meetingId={activeChatMeetingId}
          simId={simId!}
          myRoleId={myRole.id}
          myCountryCode={myRole.country_code}
          myCharacterName={myRole.character_name}
          onClose={() => { setActiveChatMeetingId(null); setDataVersion(v => v + 1) }}
        />
      )}
    </div>
  )
}

/* ── Tab: Actions ──────────────────────────────────────────────────────── */

function TabActions({roleActions, currentPhase, onSelectAction, simId, countryId, roleId, dataVersion, nuclearActionsData, parentOrgIds, parentSimRun, onOpenChat}:{
  roleActions:string[]; currentPhase:string; onSelectAction:(id:string)=>void
  simId:string; countryId:string; roleId:string; dataVersion?:number
  nuclearActionsData?:Record<string, unknown>[]
  parentOrgIds?:Set<string>
  parentSimRun?:SimRun|null
  onOpenChat?:(meetingId:string)=>void
}) {
  const avail = new Set(roleActions)
  const [reviewTxn, setReviewTxn] = useState<string|null>(null)
  const [reviewAgr, setReviewAgr] = useState<string|null>(null)
  const [signingAgr, setSigningAgr] = useState<string|null>(null)

  // Use org IDs from parent (already loaded in loadData) — no duplicate fetch
  const myOrgIds = parentOrgIds ?? new Set<string>()

  /* Realtime: meeting invitations for this role */
  const { data: meetingInvitationsRaw } = useRealtimeTable<Record<string, unknown>>(
    'meeting_invitations', simId,
    { filter: 'status=eq.pending' },
  )
  // Filter: 1:1 where I'm invitee, or org where I'm a member
  const myMeetingInvitations = (meetingInvitationsRaw as unknown as {
    id:string; invitation_type:string; inviter_role_id:string; inviter_country_code:string;
    invitee_role_id:string|null; org_id:string|null; org_name:string|null;
    message:string; theme:string|null; expires_at:string; responses:Record<string,unknown>;
  }[]).filter(inv => {
    if (inv.inviter_role_id === roleId) return false
    if (inv.invitation_type === 'one_on_one') return inv.invitee_role_id === roleId
    // Org invitations: only if I'm a member of that org
    return inv.org_id ? myOrgIds.has(inv.org_id) : false
  }).filter(inv => {
    // Check not expired
    return new Date(inv.expires_at).getTime() > Date.now()
  }).filter(inv => {
    // Check not already responded
    return !(inv.responses && (inv.responses as Record<string,unknown>)[roleId])
  })

  const [respondingTo, setRespondingTo] = useState<string|null>(null)
  const [meetingResponse, setMeetingResponse] = useState<string>('')
  const [meetingMessage, setMeetingMessage] = useState('')
  const [meetingSubmitting, setMeetingSubmitting] = useState(false)

  const handleMeetingResponse = async (invId: string, response: string, msg: string) => {
    setMeetingSubmitting(true)
    try {
      const result = await submitAction(simId, 'respond_meeting', roleId, countryId, {
        invitation_id: invId, response, message: msg,
      })
      console.log('[meeting] respond result:', result)
      setRespondingTo(null)
      setMeetingMessage('')
      // Auto-open chat when accepting a meeting
      if (response === 'accept' && onOpenChat) {
        const meetingId = result?.meeting_id as string
        if (meetingId) {
          onOpenChat(meetingId)
        } else {
          // Fallback: check the invitation for meeting_id
          const { data: inv } = await supabase.from('meeting_invitations')
            .select('meeting_id').eq('id', invId).limit(1)
          if (inv?.[0]?.meeting_id) {
            onOpenChat(inv[0].meeting_id as string)
          }
        }
        // Refresh active meetings list
        getActiveMeetings(simId, roleId).then(setActiveMeetings).catch(() => {})
      }
    } catch (err) { console.error('[meeting] respond failed:', err) }
    finally { setMeetingSubmitting(false) }
  }

  /* Active meetings for this role — for "Open Chat" buttons */
  const [activeMeetings, setActiveMeetings] = useState<MeetingData[]>([])
  useEffect(() => {
    getActiveMeetings(simId, roleId).then(setActiveMeetings).catch(() => {})
  }, [simId, roleId, dataVersion])

  /* Realtime hooks replace 5s polling for pending transactions + agreements */
  const { data: pendingTxnsRaw } = useRealtimeTable<Record<string, unknown>>(
    'exchange_transactions', simId,
    { columns: 'id,proposer,counterpart,offer,request,terms,created_at', filter: 'status=eq.pending', eq: { counterpart: countryId } },
  )
  const pendingTxns = pendingTxnsRaw as unknown as {id:string;proposer:string;offer:Record<string,unknown>;request:Record<string,unknown>;terms:string;created_at:string}[]

  const { data: allProposedAgr } = useRealtimeTable<Record<string, unknown>>(
    'agreements', simId,
    { columns: 'id,agreement_name,agreement_type,proposer_country_code,signatories,terms,signatures', eq: { status: 'proposed' } },
  )
  // Client-side filter: only agreements where this country is a signatory and hasn't signed yet
  const pendingAgreements = (allProposedAgr as unknown as {id:string;agreement_name:string;agreement_type:string;proposer_country_code:string;signatories:string[];terms:string;signatures:Record<string,unknown>}[])
    .filter(a => {
      if (!Array.isArray(a.signatories) || !a.signatories.includes(countryId)) return false
      const sigs = (a.signatures as Record<string,{confirmed?:boolean}>) || {}
      return !sigs[countryId]?.confirmed
    })

  // Leadership votes — realtime subscription for change_leader voting
  const { data: leadershipVotesRaw } = useRealtimeTable<Record<string, unknown>>(
    'leadership_votes', simId,
    { eq: { country_code: countryId }, columns: '*' },
  )
  const activeVote = leadershipVotesRaw.find(v => v.status === 'voting') as {
    id:string; phase:string; status:string; country_code:string; initiated_by:string;
    target_role:string; votes:Record<string,string>; required_majority:number;
    expires_at:string|null;
  } | undefined
  const hasVotedInActiveVote = activeVote ? !!(activeVote.votes && activeVote.votes[roleId]) : false

  // Leadership vote countdown
  const [leaderVoteCountdown, setLeaderVoteCountdown] = useState<number|null>(null)
  useEffect(() => {
    if (!activeVote?.expires_at) { setLeaderVoteCountdown(null); return }
    const tick = () => {
      const rem = Math.max(0, (new Date(activeVote.expires_at!).getTime() - Date.now()) / 1000)
      setLeaderVoteCountdown(rem)
    }
    tick()
    const iv = setInterval(tick, 1000)
    return () => clearInterval(iv)
  }, [activeVote?.id, activeVote?.expires_at])

  // Leadership vote state
  const [votingOnLeader, setVotingOnLeader] = useState<string|null>(null)
  const [leaderVoteSubmitting, setLeaderVoteSubmitting] = useState(false)
  const [selectedCandidate, setSelectedCandidate] = useState<string>('')
  const [countryRoles, setCountryRoles] = useState<{id:string;character_name:string;position_type:string}[]>([])
  useEffect(() => {
    supabase.from('roles').select('id,character_name,position_type')
      .eq('sim_run_id', simId).eq('country_code', countryId).eq('status', 'active')
      .then(({ data }) => { if (data) setCountryRoles(data) })
  }, [simId, countryId, dataVersion])

  const handleLeaderVote = async (voteId: string, vote: string) => {
    setLeaderVoteSubmitting(true)
    try {
      const token = await getToken()
      const API_BASE = import.meta.env.VITE_API_URL ?? ''
      await fetch(`${API_BASE}/api/sim/${simId}/leadership-votes/${voteId}/cast`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ role_id: roleId, vote }),
      })
      setVotingOnLeader(null)
    } catch (e) { console.error(e) }
    finally { setLeaderVoteSubmitting(false) }
  }

  // Nuclear authorization/interception — passed from parent (no duplicate subscription)
  const nuclearActions = (nuclearActionsData ?? []) as unknown as {
    id:string; action_type:string; country_code:string; status:string;
    authorizer_1_role:string|null; authorizer_2_role:string|null;
    authorizer_1_response:string|null; authorizer_2_response:string|null;
    payload:Record<string,unknown>; timer_started_at:string|null;
    timer_duration_sec:number|null; interception_responses:Record<string,unknown>|null;
  }[]

  // Authorization cards: pending nuclear actions where this role is an authorizer and hasn't responded
  const [authRoleForCountry, setAuthRoleForCountry] = useState<string|null>(null)
  const [authorizingId, setAuthorizingId] = useState<string|null>(null)
  const [authSubmitting, setAuthSubmitting] = useState(false)
  const [interceptingId, setInterceptingId] = useState<string|null>(null)
  const [interceptSubmitting, setInterceptSubmitting] = useState(false)

  // Determine what role name this role maps to for authorization
  useEffect(() => {
    // Load the role's position_type to check against authorizer roles
    supabase.from('roles').select('id, position_type')
      .eq('sim_run_id', simId).eq('id', roleId).limit(1)
      .then(({ data }) => {
        if (data?.[0]) {
          // The authorizer roles in nuclear_actions are character role IDs like 'shield', 'rampart' etc.
          // For the human interface, we match by role ID directly
          setAuthRoleForCountry(data[0].id)
        }
      })
  }, [simId, roleId])

  const pendingAuthorizations = nuclearActions.filter(a =>
    a.status === 'awaiting_authorization' &&
    a.country_code === countryId &&
    ((a.authorizer_1_role === roleId && !a.authorizer_1_response) ||
     (a.authorizer_2_role === roleId && !a.authorizer_2_response))
  )

  // Interception cards: T3+ countries with pending interception
  const pendingInterceptions = nuclearActions.filter(a =>
    a.status === 'awaiting_interception' &&
    a.country_code !== countryId && // not the launcher
    !(a.interception_responses && (a.interception_responses as Record<string,unknown>)[countryId]) // haven't responded
  )
  // Only show if our country is T3+ — check nuclearLevel from parent state via simple query
  const [myNuclearLevel, setMyNuclearLevel] = useState(0)
  useEffect(() => {
    supabase.from('countries').select('nuclear_level, nuclear_confirmed')
      .eq('sim_run_id', simId).eq('id', countryId).limit(1)
      .then(({ data }) => {
        if (data?.[0]?.nuclear_confirmed && (data[0].nuclear_level ?? 0) >= 2) {
          setMyNuclearLevel(data[0].nuclear_level)
        }
      })
  }, [simId, countryId, dataVersion])

  const visibleInterceptions = myNuclearLevel >= 2 ? pendingInterceptions : []

  // ── Columbia Elections ──────────────────────────────────────────────
  const isColumbia = countryId === 'columbia'

  // Realtime: nominations for this sim
  const { data: electionNominationsRaw } = useRealtimeTable<Record<string, unknown>>(
    'election_nominations', simId,
    { columns: '*', enabled: isColumbia },
  )
  const electionNominations = electionNominationsRaw as unknown as {
    id:string; election_type:string; election_round:number; role_id:string; camp:string
  }[]

  // Realtime: votes for this sim (just to check if I voted)
  const { data: electionVotesRaw } = useRealtimeTable<Record<string, unknown>>(
    'election_votes', simId,
    { columns: 'id,election_type,voter_role_id', enabled: isColumbia },
  )
  const electionVotes = electionVotesRaw as unknown as {
    id:string; election_type:string; voter_role_id:string
  }[]

  // Realtime: results
  const { data: electionResultsRaw } = useRealtimeTable<Record<string, unknown>>(
    'election_results', simId,
    { columns: '*', enabled: isColumbia },
  )
  const electionResults = electionResultsRaw as unknown as {
    id:string; election_type:string; election_round:number; winner_role_id:string|null
  }[]

  // Derive key_events and current_round from parent's realtime simRun (no duplicate queries)
  const keyEventsData = useMemo(() => {
    const ke = parentSimRun?.key_events as {type:string;subtype?:string;round?:number;nominations_round?:number;name?:string}[] | undefined
    if (!ke) return []
    return ke.filter(e => e.type === 'election').map(e => ({
      type: e.type, subtype: e.subtype ?? '', round: e.round ?? 0,
      nominations_round: e.nominations_round ?? 0, name: e.name ?? '',
    }))
  }, [parentSimRun?.key_events])

  const currentRound = parentSimRun?.current_round ?? 0

  // Find active election events for this round
  const activeNominationEvent = isColumbia ? keyEventsData.find(e => e.nominations_round === currentRound) : undefined
  const activeElectionEvent = isColumbia ? keyEventsData.find(e => e.round === currentRound) : undefined

  // Check if already nominated
  const myNomination = activeNominationEvent
    ? electionNominations.find(n => n.role_id === roleId && n.election_type === activeNominationEvent.subtype)
    : undefined

  // Check if already voted
  const myElectionVote = activeElectionEvent
    ? electionVotes.find(v => v.voter_role_id === roleId && v.election_type === activeElectionEvent.subtype)
    : undefined

  // Check if election already resolved
  const electionResolved = activeElectionEvent
    ? electionResults.find(r => r.election_type === activeElectionEvent.subtype && r.election_round === activeElectionEvent.round)
    : undefined

  // Candidates for the active election
  const electionCandidates = activeElectionEvent
    ? electionNominations.filter(n => n.election_type === activeElectionEvent.subtype && n.election_round === activeElectionEvent.round)
    : []

  // Election UI state
  const [showElectionPanel, setShowElectionPanel] = useState<'nominate'|'vote'|'results'|null>(null)
  const [electionSubmitting, setElectionSubmitting] = useState(false)
  const [selectedElectionCandidate, setSelectedElectionCandidate] = useState<string>('')

  // Check if nominations are open/closed (moderator controls)
  // Derive nomination state from parent's realtime simRun (proper columns, not JSONB)
  const autoApprove = !!parentSimRun?.auto_approve
  const nominationsClosed = activeNominationEvent ? parentSimRun?.nominations_closed === true : false
  const nominationsOpen = activeNominationEvent ? (!nominationsClosed && (parentSimRun?.nominations_open === true || autoApprove)) : false

  // Check if this role is a sitting parliament member (cannot nominate for midterms unless seat is for reelection)
  const [isParliamentMember, setIsParliamentMember] = useState(false)
  const [isSeatForReelection, setIsSeatForReelection] = useState(false)
  useEffect(() => {
    if (!simId || !isColumbia) return
    supabase.from('org_memberships').select('role_in_org')
      .eq('sim_run_id', simId).eq('org_id', 'columbia_parliament').eq('country_code', countryId)
      .then(({ data }) => {
        const myMembership = (data || []).find((m: Record<string,unknown>) => {
          // Need to check by role — but org_memberships are by country, not role
          // For now: check if role_in_org includes 'reelection'
          return m.role_in_org === 'member_reelection'
        })
        // Simplified: any parliament member that's NOT up for reelection can't run for midterms
        const members = data || []
        setIsParliamentMember(members.length > 0)
        setIsSeatForReelection(members.some((m: Record<string,unknown>) => m.role_in_org === 'member_reelection'))
      })
  }, [simId, isColumbia, countryId])

  const canNominateForMidterm = !isParliamentMember || isSeatForReelection

  // Local nomination state for optimistic updates (realtime may be slow)
  const [localNominated, setLocalNominated] = useState<boolean|null>(null)

  // Show election in expected actions
  // Combine DB nomination with local optimistic state
  const isNominated = localNominated === true || (localNominated === null && !!myNomination)
  const showNomination = isColumbia && activeNominationEvent && !isNominated && nominationsOpen
    && (activeNominationEvent.subtype !== 'parliamentary_midterm' || canNominateForMidterm)
  // Derive election open state from parent's realtime simRun (proper column)
  const electionOpen = activeElectionEvent ? (parentSimRun?.election_open === true || autoApprove) : false

  const showElectionVote = isColumbia && activeElectionEvent && !myElectionVote && !electionResolved && electionCandidates.length > 0 && electionOpen

  // ── Early returns for review screens (AFTER all hooks) ──────────────
  // If reviewing a transaction, show the review screen
  const txnToReview = reviewTxn ? pendingTxns.find(t=>t.id===reviewTxn) : null
  if (txnToReview) {
    return <TransactionReview txn={txnToReview} simId={simId} countryId={countryId} roleId={roleId}
      onClose={()=>setReviewTxn(null)}
      onDone={()=>{setReviewTxn(null)}} />
  }

  // Agreement signing handler
  const handleSignAgreement = async (agrId:string, confirm:boolean) => {
    setSigningAgr(agrId)
    try {
      await submitAction(simId,'sign_agreement',roleId,countryId,{
        agreement_id:agrId, confirm, comments:'',
      })
    } catch(e) { alert(e instanceof Error?e.message:'Failed') }
    finally { setSigningAgr(null) }
  }

  // If reviewing an agreement, show the review screen
  const agrToReview = reviewAgr ? pendingAgreements.find(a=>a.id===reviewAgr) : null
  if (agrToReview) {
    const typeLabel = AGREEMENT_TYPES.find(t=>t.value===agrToReview.agreement_type)?.label ?? agrToReview.agreement_type
    const relationLabel = AGREEMENT_TYPES.find(t=>t.value===agrToReview.agreement_type)?.relation ?? ''
    const sigs = agrToReview.signatures as Record<string,{confirmed?:boolean;role_id?:string;signed_at?:string}>
    const signedCountries = Object.entries(sigs).filter(([,s])=>s?.confirmed).map(([cc])=>cc)

    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="font-heading text-h2 text-text-primary">Agreement Proposal</h2>
          <button onClick={()=>setReviewAgr(null)} className="font-body text-caption text-text-secondary hover:text-text-primary px-3 py-1 rounded border border-border">← Back</button>
        </div>

        <div className="bg-card border-2 border-action/20 rounded-lg p-6 space-y-4">
          <div className="flex items-center gap-3">
            <span className="font-heading text-h3 text-text-primary">{agrToReview.agreement_name}</span>
            <span className="font-body text-caption bg-action/10 text-action px-2 py-0.5 rounded capitalize">{typeLabel}</span>
          </div>

          <div className="font-body text-caption text-text-secondary">
            Proposed by <strong className="text-text-primary">{agrToReview.proposer_country_code}</strong> ·
            Sets relationship to <strong className="text-text-primary">{relationLabel}</strong>
          </div>

          <div className="font-body text-caption text-text-secondary">
            Signatories: {(agrToReview.signatories||[]).map(s=>
              <span key={s} className={`inline-block mr-2 ${signedCountries.includes(s)?'text-success':'text-text-primary'}`}>
                {s}{signedCountries.includes(s)?' ✓':''}
              </span>
            )}
          </div>

          {agrToReview.terms&&<div className="bg-base border border-border rounded-lg p-4">
            <h3 className="font-heading text-caption text-text-secondary uppercase tracking-wider mb-2">Terms</h3>
            <p className="font-body text-body-sm text-text-primary leading-relaxed whitespace-pre-wrap">{agrToReview.terms}</p>
          </div>}
        </div>

        <div className="flex items-center gap-3">
          <button onClick={async()=>{
            setSigningAgr(agrToReview.id)
            await handleSignAgreement(agrToReview.id,true)
            setReviewAgr(null)
          }} disabled={signingAgr===agrToReview.id}
            className="bg-success text-white font-body text-body-sm font-medium px-6 py-2.5 rounded-lg hover:bg-success/90 disabled:opacity-50 transition-colors">
            {signingAgr===agrToReview.id?'Signing...':'Sign Agreement'}</button>
          <button onClick={async()=>{
            setSigningAgr(agrToReview.id)
            await handleSignAgreement(agrToReview.id,false)
            setReviewAgr(null)
          }} disabled={signingAgr===agrToReview.id}
            className="bg-danger/10 text-danger font-body text-body-sm font-medium px-6 py-2.5 rounded-lg hover:bg-danger/20 transition-colors">
            Decline</button>
          <button onClick={()=>setReviewAgr(null)} className="font-body text-body-sm text-text-secondary hover:text-text-primary px-4 py-2.5">Cancel</button>
        </div>
      </div>
    )
  }

  const handleSelfNominate = async () => {
    if (!activeNominationEvent) return
    setElectionSubmitting(true)
    try {
      const res = await submitAction(simId, 'self_nominate', roleId, countryId, {
        election_type: activeNominationEvent.subtype,
        election_round: activeNominationEvent.round,
      })
      if (res.success) {
        setLocalNominated(true)
      } else {
        alert(res.narrative || 'Nomination failed')
      }
    } catch (e) { alert(e instanceof Error ? e.message : 'Nomination failed') }
    finally { setElectionSubmitting(false) }
  }

  const handleWithdrawNomination = async () => {
    if (!activeNominationEvent) return
    setElectionSubmitting(true)
    try {
      const res = await submitAction(simId, 'withdraw_nomination', roleId, countryId, {
        election_type: activeNominationEvent.subtype,
      })
      if (res.success) {
        setLocalNominated(false)
      } else {
        alert(res.narrative || 'Withdrawal failed')
      }
    } catch (e) { alert(e instanceof Error ? e.message : 'Withdrawal failed') }
    finally { setElectionSubmitting(false) }
  }

  const handleCastElectionVote = async () => {
    if (!activeElectionEvent || !selectedElectionCandidate) return
    setElectionSubmitting(true)
    try {
      await submitAction(simId, 'cast_election_vote', roleId, countryId, {
        candidate_role_id: selectedElectionCandidate,
        election_type: activeElectionEvent.subtype,
      })
      setShowElectionPanel(null)
      setSelectedElectionCandidate('')
    } catch (e) { alert(e instanceof Error ? e.message : 'Vote failed') }
    finally { setElectionSubmitting(false) }
  }

  const handleAuthorize = async (actionId: string, confirm: boolean, rationale: string) => {
    setAuthSubmitting(true)
    try {
      await submitAction(simId, 'nuclear_authorize', roleId, countryId, {
        nuclear_action_id: actionId, confirm, rationale,
      })
      setAuthorizingId(null)
    } catch (e) { alert(e instanceof Error ? e.message : 'Failed') }
    finally { setAuthSubmitting(false) }
  }

  const handleIntercept = async (actionId: string, intercept: boolean, rationale: string) => {
    setInterceptSubmitting(true)
    try {
      await submitAction(simId, 'nuclear_intercept', roleId, countryId, {
        nuclear_action_id: actionId, intercept, rationale,
      })
      setInterceptingId(null)
    } catch (e) { alert(e instanceof Error ? e.message : 'Failed') }
    finally { setInterceptSubmitting(false) }
  }

  // Leadership vote detail panel
  if (votingOnLeader && activeVote) {
    const hosRole = countryRoles.find(r => r.id === activeVote.target_role)
    const hosName = hosRole?.character_name ?? activeVote.target_role
    const votesObj = activeVote.votes || {}
    const votesCast = Object.keys(votesObj).length
    const mm = leaderVoteCountdown !== null ? String(Math.floor(leaderVoteCountdown / 60)).padStart(2, '0') : '--'
    const ss = leaderVoteCountdown !== null ? String(Math.floor(leaderVoteCountdown % 60)).padStart(2, '0') : '--'

    if (activeVote.phase === 'removal') {
      return (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-heading text-h2 text-text-primary">Remove Head of State</h2>
            <button onClick={() => setVotingOnLeader(null)}
              className="font-body text-caption text-text-secondary hover:text-text-primary px-3 py-1 rounded border border-border">
              ← Back
            </button>
          </div>

          <div className="bg-danger/5 border border-danger/20 rounded-lg p-4">
            <p className="font-body text-body-sm text-text-primary">
              Vote to remove <strong className="text-danger">{hosName}</strong> as Head of State.
              Need <strong>{activeVote.required_majority}</strong> YES votes from non-HoS citizens.
            </p>
            <p className="font-body text-caption text-text-secondary mt-1">
              {votesCast} vote{votesCast !== 1 ? 's' : ''} cast
            </p>
          </div>

          <div className="grid grid-cols-2 gap-3 text-center">
            <div className="bg-base rounded-lg p-3">
              <div className="font-data text-data-lg text-text-primary">{mm}:{ss}</div>
              <div className="font-body text-caption text-text-secondary">Time remaining</div>
            </div>
            <div className="bg-base rounded-lg p-3">
              <div className="font-data text-data-lg text-danger">{activeVote.required_majority}</div>
              <div className="font-body text-caption text-text-secondary">YES votes needed</div>
            </div>
          </div>

          <div className="flex gap-3">
            <button onClick={() => handleLeaderVote(activeVote.id, 'yes')} disabled={leaderVoteSubmitting}
              className="flex-1 bg-danger/10 text-danger font-body text-body-sm font-medium py-2.5 rounded-lg hover:bg-danger/20 disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
              Yes — Remove
            </button>
            <button onClick={() => handleLeaderVote(activeVote.id, 'no')} disabled={leaderVoteSubmitting}
              className="flex-1 bg-success/10 text-success font-body text-body-sm font-medium py-2.5 rounded-lg hover:bg-success/20 disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
              No — Keep
            </button>
          </div>
        </div>
      )
    }

    // Election phase
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="font-heading text-h2 text-text-primary">Elect New Head of State</h2>
          <button onClick={() => setVotingOnLeader(null)}
            className="font-body text-caption text-text-secondary hover:text-text-primary px-3 py-1 rounded border border-border">
            ← Back
          </button>
        </div>

        <div className="bg-action/5 border border-action/20 rounded-lg p-4">
          <p className="font-body text-body-sm text-text-primary">
            Select a candidate. Need <strong className="text-action">{activeVote.required_majority}</strong> votes for majority.
          </p>
          <p className="font-body text-caption text-text-secondary mt-1">
            {votesCast} vote{votesCast !== 1 ? 's' : ''} cast
          </p>
        </div>

        <div className="grid grid-cols-2 gap-3 text-center">
          <div className="bg-base rounded-lg p-3">
            <div className="font-data text-data-lg text-text-primary">{mm}:{ss}</div>
            <div className="font-body text-caption text-text-secondary">Time remaining</div>
          </div>
          <div className="bg-base rounded-lg p-3">
            <div className="font-data text-data-lg text-action">{activeVote.required_majority}</div>
            <div className="font-body text-caption text-text-secondary">Votes needed</div>
          </div>
        </div>

        <div className="bg-card border border-border rounded-lg divide-y divide-border">
          {countryRoles.map(r => (
            <label key={r.id} className={`flex items-center gap-3 px-4 py-3 cursor-pointer transition-colors ${
              selectedCandidate === r.id ? 'bg-action/5' : 'hover:bg-base'
            }`}>
              <input type="radio" name="candidate" value={r.id} checked={selectedCandidate === r.id}
                onChange={() => setSelectedCandidate(r.id)} className="accent-action"/>
              <span className="font-body text-body-sm text-text-primary flex-1">{r.character_name}</span>
              <span className="font-body text-caption text-text-secondary capitalize">
                {r.position_type?.replace(/_/g,' ')}
              </span>
            </label>
          ))}
        </div>

        <button onClick={() => { if (selectedCandidate) handleLeaderVote(activeVote.id, selectedCandidate) }}
          disabled={!selectedCandidate || leaderVoteSubmitting}
          className="w-full bg-action text-white font-body text-body-sm font-medium py-2.5 rounded-lg hover:bg-action/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
          {leaderVoteSubmitting ? 'Submitting...' : 'Cast Vote'}
        </button>
      </div>
    )
  }

  // Authorization detail panel
  const authAction = authorizingId ? nuclearActions.find(a => a.id === authorizingId) : null
  if (authAction) {
    const missiles = (authAction.payload?.changes as Record<string,unknown>)?.missiles as {missile_unit_code:string;target_global_row:number;target_global_col:number}[] ?? []
    return (
      <div style={{
        backgroundColor:'#0A0E1A',borderRadius:'0.5rem',padding:'1.5rem',
        border:'2px solid rgba(255,60,20,0.4)',
      }}>
        <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',marginBottom:'1rem'}}>
          <h2 style={{fontFamily:'JetBrains Mono, monospace',fontSize:'1.1rem',color:'#FF3C14',
            textTransform:'uppercase',letterSpacing:'0.1em'}}>{'\u26A0'} Nuclear Launch Authorization</h2>
          <button onClick={() => setAuthorizingId(null)} style={{
            fontFamily:'DM Sans, sans-serif',fontSize:'0.75rem',color:'#9CA3AF',
            cursor:'pointer',border:'1px solid rgba(255,255,255,0.15)',borderRadius:'0.25rem',
            padding:'0.25rem 0.5rem',backgroundColor:'transparent',
          }}>{'\u2190'} Back</button>
        </div>

        <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:'1rem',marginBottom:'1.5rem'}}>
          <div style={{padding:'0.75rem',borderRadius:'0.25rem',border:'1px solid rgba(255,255,255,0.1)'}}>
            <div style={{fontFamily:'JetBrains Mono, monospace',fontSize:'0.65rem',color:'#9CA3AF',textTransform:'uppercase'}}>Launcher</div>
            <div style={{fontFamily:'JetBrains Mono, monospace',fontSize:'1rem',color:'#FF3C14'}}>{authAction.country_code.toUpperCase()}</div>
          </div>
          <div style={{padding:'0.75rem',borderRadius:'0.25rem',border:'1px solid rgba(255,255,255,0.1)'}}>
            <div style={{fontFamily:'JetBrains Mono, monospace',fontSize:'0.65rem',color:'#9CA3AF',textTransform:'uppercase'}}>Missiles</div>
            <div style={{fontFamily:'JetBrains Mono, monospace',fontSize:'1rem',color:'#FF3C14'}}>{missiles.length}</div>
          </div>
        </div>

        <div style={{marginBottom:'1.5rem'}}>
          <div style={{fontFamily:'JetBrains Mono, monospace',fontSize:'0.65rem',color:'#9CA3AF',textTransform:'uppercase',marginBottom:'0.5rem'}}>Targets</div>
          {missiles.map((m, i) => (
            <div key={i} style={{display:'flex',alignItems:'center',gap:'0.4rem',fontFamily:'JetBrains Mono, monospace',fontSize:'0.8rem',color:'#D1D5DB',marginBottom:'0.35rem'}}>
              <UnitIcon type="strategic_missile" size={16}/> {'\u2192'} ({m.target_global_row},{m.target_global_col}) — <span style={{color:'#FF3C14'}}>{hexCountryName(m.target_global_row, m.target_global_col)}</span>
            </div>
          ))}
        </div>

        <div style={{display:'flex',gap:'1rem'}}>
          <button onClick={() => handleAuthorize(authAction.id, true, 'Authorization confirmed by authorized officer')}
            disabled={authSubmitting}
            style={{
              flex:1,padding:'0.75rem',borderRadius:'0.375rem',cursor:'pointer',
              backgroundColor:'rgba(255,60,20,0.2)',border:'2px solid #FF3C14',
              color:'#FF3C14',fontFamily:'JetBrains Mono, monospace',
              fontSize:'0.85rem',fontWeight:700,textTransform:'uppercase',
              letterSpacing:'0.1em',opacity:authSubmitting?0.5:1,
            }}>AUTHORIZE</button>
          <button onClick={() => handleAuthorize(authAction.id, false, 'Authorization rejected by authorized officer')}
            disabled={authSubmitting}
            style={{
              flex:1,padding:'0.75rem',borderRadius:'0.375rem',cursor:'pointer',
              backgroundColor:'rgba(0,255,65,0.1)',border:'2px solid #00FF41',
              color:'#00FF41',fontFamily:'JetBrains Mono, monospace',
              fontSize:'0.85rem',fontWeight:700,textTransform:'uppercase',
              letterSpacing:'0.1em',opacity:authSubmitting?0.5:1,
            }}>REJECT</button>
        </div>
      </div>
    )
  }

  // Interception detail panel
  const intAction = interceptingId ? nuclearActions.find(a => a.id === interceptingId) : null
  if (intAction) {
    const missiles = (intAction.payload?.changes as Record<string,unknown>)?.missiles as {missile_unit_code:string;target_global_row:number;target_global_col:number}[] ?? []
    return (
      <div style={{
        backgroundColor:'#0A0E1A',borderRadius:'0.5rem',padding:'1.5rem',
        border:'2px solid rgba(255,60,20,0.4)',
      }}>
        <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',marginBottom:'1rem'}}>
          <h2 style={{fontFamily:'JetBrains Mono, monospace',fontSize:'1.1rem',color:'#FF3C14',
            textTransform:'uppercase',letterSpacing:'0.1em'}}>{'\u26A0'} Nuclear Interception Decision</h2>
          <button onClick={() => setInterceptingId(null)} style={{
            fontFamily:'DM Sans, sans-serif',fontSize:'0.75rem',color:'#9CA3AF',
            cursor:'pointer',border:'1px solid rgba(255,255,255,0.15)',borderRadius:'0.25rem',
            padding:'0.25rem 0.5rem',backgroundColor:'transparent',
          }}>{'\u2190'} Back</button>
        </div>

        <div style={{display:'grid',gridTemplateColumns:'1fr 1fr 1fr',gap:'1rem',marginBottom:'1.5rem'}}>
          <div style={{padding:'0.75rem',borderRadius:'0.25rem',border:'1px solid rgba(255,255,255,0.1)'}}>
            <div style={{fontFamily:'JetBrains Mono, monospace',fontSize:'0.65rem',color:'#9CA3AF',textTransform:'uppercase'}}>Launcher</div>
            <div style={{fontFamily:'JetBrains Mono, monospace',fontSize:'1rem',color:'#FF3C14'}}>{intAction.country_code.toUpperCase()}</div>
          </div>
          <div style={{padding:'0.75rem',borderRadius:'0.25rem',border:'1px solid rgba(255,255,255,0.1)'}}>
            <div style={{fontFamily:'JetBrains Mono, monospace',fontSize:'0.65rem',color:'#9CA3AF',textTransform:'uppercase'}}>Missiles</div>
            <div style={{fontFamily:'JetBrains Mono, monospace',fontSize:'1rem',color:'#FF3C14'}}>{missiles.length}</div>
          </div>
          <div style={{padding:'0.75rem',borderRadius:'0.25rem',border:'1px solid rgba(255,255,255,0.1)'}}>
            <div style={{fontFamily:'JetBrains Mono, monospace',fontSize:'0.65rem',color:'#9CA3AF',textTransform:'uppercase'}}>Intercept Prob</div>
            <div style={{fontFamily:'JetBrains Mono, monospace',fontSize:'1rem',color:'#F59E0B'}}>25% / AD</div>
          </div>
        </div>

        <div style={{marginBottom:'1rem'}}>
          <div style={{fontFamily:'JetBrains Mono, monospace',fontSize:'0.65rem',color:'#9CA3AF',textTransform:'uppercase',marginBottom:'0.5rem'}}>Targets</div>
          {missiles.map((m, i) => (
            <div key={i} style={{display:'flex',alignItems:'center',gap:'0.4rem',fontFamily:'JetBrains Mono, monospace',fontSize:'0.8rem',color:'#D1D5DB',marginBottom:'0.35rem'}}>
              <UnitIcon type="strategic_missile" size={16}/> {'\u2192'} ({m.target_global_row},{m.target_global_col}) — <span style={{color:'#FF3C14'}}>{hexCountryName(m.target_global_row, m.target_global_col)}</span>
            </div>
          ))}
        </div>

        <div style={{
          padding:'0.75rem',borderRadius:'0.25rem',border:'1px solid rgba(245,158,11,0.3)',
          backgroundColor:'rgba(245,158,11,0.05)',marginBottom:'1.5rem',
        }}>
          <p style={{fontFamily:'JetBrains Mono, monospace',fontSize:'0.7rem',color:'#F59E0B'}}>
            WARNING: Intercepting reveals your AD capability and sides you against {intAction.country_code.toUpperCase()}.
          </p>
        </div>

        <div style={{display:'flex',gap:'1rem'}}>
          <button onClick={() => handleIntercept(intAction.id, true, 'Interception ordered')}
            disabled={interceptSubmitting}
            style={{
              flex:1,padding:'0.75rem',borderRadius:'0.375rem',cursor:'pointer',
              backgroundColor:'rgba(255,60,20,0.2)',border:'2px solid #FF3C14',
              color:'#FF3C14',fontFamily:'JetBrains Mono, monospace',
              fontSize:'0.85rem',fontWeight:700,textTransform:'uppercase',
              letterSpacing:'0.1em',opacity:interceptSubmitting?0.5:1,
            }}>INTERCEPT</button>
          <button onClick={() => handleIntercept(intAction.id, false, 'Declined interception')}
            disabled={interceptSubmitting}
            style={{
              flex:1,padding:'0.75rem',borderRadius:'0.375rem',cursor:'pointer',
              backgroundColor:'rgba(255,255,255,0.05)',border:'2px solid rgba(255,255,255,0.2)',
              color:'#9CA3AF',fontFamily:'JetBrains Mono, monospace',
              fontSize:'0.85rem',fontWeight:700,textTransform:'uppercase',
              letterSpacing:'0.1em',opacity:interceptSubmitting?0.5:1,
            }}>DECLINE</button>
        </div>
      </div>
    )
  }

  // ── Election Detail Panels (rendered before main actions list) ────────
  if (showElectionPanel === 'nominate' && activeNominationEvent) {
    const elType = activeNominationEvent.subtype === 'presidential' ? 'Presidential Election' : 'Mid-Term Parliamentary Election'
    const currentNominees = electionNominations.filter(n =>
      n.election_type === activeNominationEvent.subtype && n.election_round === activeNominationEvent.round
    )
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="font-heading text-h2 text-text-primary">Columbia Elections — Nominations</h2>
          <button onClick={() => setShowElectionPanel(null)}
            className="font-body text-caption text-text-secondary hover:text-text-primary px-3 py-1 rounded border border-border">
            ← Back
          </button>
        </div>

        <div className={`${nominationsClosed ? 'bg-base' : 'bg-action/5'} border ${nominationsClosed ? 'border-border' : 'border-action/20'} rounded-lg p-4 space-y-2`}>
          <p className="font-body text-body-sm text-text-primary">
            <strong className="text-action">{elType}</strong> — Election Round {activeNominationEvent.round}
          </p>
          <p className="font-body text-caption text-text-secondary">
            {nominationsClosed
              ? `Nominations are closed. The election will take place in Round ${activeNominationEvent.round}.`
              : `Nominations are open this round. The election will take place in Round ${activeNominationEvent.round}.`
            }
          </p>
          <p className="font-body text-caption text-text-secondary">
            Opposition candidates represent 2 votes each. Under certain political and economic circumstances, their popular support may grow to 3 votes each.
          </p>
        </div>

        {currentNominees.length > 0 && (
          <div className="bg-card border border-border rounded-lg p-4">
            <h3 className="font-heading text-caption text-text-secondary uppercase tracking-wider mb-3">
              {nominationsClosed ? 'Candidates' : 'Current Nominees'}
            </h3>
            <div className="space-y-2">
              {currentNominees.map(n => (
                <div key={n.id} className="flex items-center gap-3 bg-base rounded px-3 py-2">
                  <span className="font-body text-body-sm text-text-primary font-medium capitalize">{n.role_id}</span>
                  <span className={`font-body text-caption px-2 py-0.5 rounded ${
                    n.camp === 'opposition' ? 'bg-action/10 text-action' : 'bg-text-secondary/10 text-text-secondary'
                  }`}>{n.camp === 'opposition' ? 'Opposition' : 'Government'}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {nominationsClosed ? null : !isNominated ? (
          <button onClick={handleSelfNominate} disabled={electionSubmitting}
            className="w-full bg-action text-white font-body text-body-sm font-medium py-2.5 rounded-lg hover:bg-action/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
            {electionSubmitting ? 'Submitting...' : 'Nominate Yourself'}
          </button>
        ) : (
          <div className="space-y-2">
            <div className="bg-success/10 border border-success/20 rounded-lg p-3">
              <p className="font-body text-body-sm text-success">You are nominated for this election.</p>
            </div>
            <button onClick={handleWithdrawNomination} disabled={electionSubmitting}
              className="w-full bg-danger/10 text-danger font-body text-body-sm font-medium py-2.5 rounded-lg hover:bg-danger/20 disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
              {electionSubmitting ? 'Withdrawing...' : 'Withdraw Nomination'}
            </button>
          </div>
        )}
      </div>
    )
  }

  if (showElectionPanel === 'vote' && activeElectionEvent && !electionResolved) {
    const elType = activeElectionEvent.subtype === 'presidential' ? 'Presidential Election' : 'Mid-Term Parliamentary Election'
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="font-heading text-h2 text-text-primary">Columbia Elections — Cast Your Vote</h2>
          <button onClick={() => setShowElectionPanel(null)}
            className="font-body text-caption text-text-secondary hover:text-text-primary px-3 py-1 rounded border border-border">
            ← Back
          </button>
        </div>

        <div className="bg-action/5 border border-action/20 rounded-lg p-4 space-y-2">
          <p className="font-body text-body-sm text-text-primary">
            <strong className="text-action">{elType}</strong> — Secret Ballot
          </p>
          <p className="font-body text-caption text-text-secondary">
            Select a candidate and cast your vote. Your choice will not be revealed to other participants.
          </p>
        </div>

        <div className="bg-card border border-border rounded-lg divide-y divide-border">
          {electionCandidates.map(c => (
            <label key={c.role_id} className={`flex items-center gap-3 px-4 py-3 cursor-pointer transition-colors ${
              selectedElectionCandidate === c.role_id ? 'bg-action/5' : 'hover:bg-base'
            }`}>
              <input type="radio" name="electionCandidate" value={c.role_id}
                checked={selectedElectionCandidate === c.role_id}
                onChange={() => setSelectedElectionCandidate(c.role_id)}
                className="accent-action"/>
              <span className="font-body text-body-sm text-text-primary flex-1 capitalize">{c.role_id}</span>
            </label>
          ))}
        </div>

        <button onClick={handleCastElectionVote}
          disabled={!selectedElectionCandidate || electionSubmitting}
          className="w-full bg-action text-white font-body text-body-sm font-medium py-2.5 rounded-lg hover:bg-action/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
          {electionSubmitting ? 'Submitting...' : 'Cast Vote'}
        </button>
      </div>
    )
  }

  // Election results panel
  if (showElectionPanel === 'results' && electionResolved && activeElectionEvent) {
    const elType = activeElectionEvent.subtype === 'presidential' ? 'Presidential Election' : 'Mid-Term Parliamentary Election'
    const totalVotes = electionResolved.total_votes as Record<string, number> || {}
    const totalSum = Object.values(totalVotes).reduce((s, v) => s + v, 0)
    const sortedCandidates = Object.entries(totalVotes).sort((a, b) => b[1] - a[1])
    const winner = electionResolved.winner_role_id

    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="font-heading text-h2 text-text-primary">Election Results</h2>
          <button onClick={() => setShowElectionPanel(null)}
            className="font-body text-caption text-text-secondary hover:text-text-primary px-3 py-1 rounded border border-border">
            ← Back
          </button>
        </div>

        <div className="bg-success/5 border border-success/20 rounded-lg p-4">
          <p className="font-body text-body-sm text-text-primary">
            <strong className="text-success">{elType}</strong> — Results
          </p>
          {winner && (
            <p className="font-body text-body-sm text-success font-medium mt-1 capitalize">
              Winner: {winner}
            </p>
          )}
          {!winner && (
            <p className="font-body text-body-sm text-warning font-medium mt-1">
              No candidate achieved majority
            </p>
          )}
        </div>

        <div className="bg-card border border-border rounded-lg divide-y divide-border">
          {sortedCandidates.map(([candidate, votes]) => {
            const pct = totalSum > 0 ? (votes / totalSum * 100) : 0
            const isWinner = candidate === winner
            return (
              <div key={candidate} className="px-4 py-3">
                <div className="flex items-center justify-between mb-1">
                  <span className={`font-body text-body-sm font-medium capitalize ${isWinner ? 'text-success' : 'text-text-primary'}`}>
                    {candidate} {isWinner && '— Elected'}
                  </span>
                  <span className="font-data text-caption text-text-secondary">{pct.toFixed(1)}%</span>
                </div>
                <div className="w-full bg-border rounded-full h-2">
                  <div className={`h-2 rounded-full ${isWinner ? 'bg-success' : 'bg-action/40'}`}
                    style={{ width: `${pct}%` }} />
                </div>
              </div>
            )
          })}
        </div>
      </div>
    )
  }

  const showMoveUnits = currentPhase === 'inter_round' && avail.has('move_units')
  const showLeaderVote = activeVote && !hasVotedInActiveVote ? 1 : 0
  const electionExpected = (showNomination ? 1 : 0) + (showElectionVote ? 1 : 0) + (isNominated ? 1 : 0) + (electionResolved ? 1 : 0)
  const expectedCount = pendingTxns.length + pendingAgreements.length + (showMoveUnits ? 1 : 0) + myMeetingInvitations.length
    + pendingAuthorizations.length + visibleInterceptions.length + showLeaderVote + electionExpected
  const hasExpected = expectedCount > 0

  return (
    <div className="space-y-4">
      {/* Actions Expected Now */}
      <div className={`border rounded-lg p-4 ${hasExpected?'bg-warning/10 border-warning/30':'bg-warning/5 border-warning/20'}`}>
        <h3 className="font-heading text-h3 text-warning mb-2">Actions Expected Now{hasExpected?` (${expectedCount})`:''}</h3>
        {!hasExpected
          ? <p className="font-body text-caption text-text-secondary">No urgent actions at this time.</p>
          : <div className="grid grid-cols-2 lg:grid-cols-3 gap-2">
            {showMoveUnits && (
              <button onClick={()=>onSelectAction('move_units')}
                className="text-left bg-card hover:bg-action/5 border-2 border-action/40 hover:border-action/60 rounded-lg px-4 py-3 transition-colors">
                <span className="font-body text-body-sm text-action font-bold block">Deploy & Move Units</span>
                <span className="font-body text-caption text-text-secondary">Position your forces for the next round</span>
              </button>
            )}
            {pendingAuthorizations.map(na => (
              <button key={na.id} onClick={() => setAuthorizingId(na.id)}
                style={{
                  textAlign:'left',backgroundColor:'rgba(255,60,20,0.08)',
                  border:'2px solid rgba(255,60,20,0.5)',borderRadius:'0.5rem',
                  padding:'0.75rem 1rem',cursor:'pointer',
                }}>
                <span style={{fontFamily:'JetBrains Mono, monospace',fontSize:'0.85rem',color:'#FF3C14',fontWeight:700,display:'block'}}>
                  {'\u26A0'} NUCLEAR LAUNCH AUTHORIZATION
                </span>
                <span style={{fontFamily:'DM Sans, sans-serif',fontSize:'0.75rem',color:'#D1D5DB',display:'block',marginTop:'0.25rem'}}>
                  {na.country_code.toUpperCase()} requests launch authorization — click to review
                </span>
              </button>
            ))}
            {visibleInterceptions.map(na => (
              <button key={na.id} onClick={() => setInterceptingId(na.id)}
                style={{
                  textAlign:'left',backgroundColor:'rgba(255,60,20,0.08)',
                  border:'2px solid rgba(255,60,20,0.5)',borderRadius:'0.5rem',
                  padding:'0.75rem 1rem',cursor:'pointer',
                }}>
                <span style={{fontFamily:'JetBrains Mono, monospace',fontSize:'0.85rem',color:'#FF3C14',fontWeight:700,display:'block'}}>
                  {'\u26A0'} NUCLEAR INTERCEPTION DECISION
                </span>
                <span style={{fontFamily:'DM Sans, sans-serif',fontSize:'0.75rem',color:'#D1D5DB',display:'block',marginTop:'0.25rem'}}>
                  {na.country_code.toUpperCase()} launched missiles — intercept?
                </span>
              </button>
            ))}
            {activeVote && !hasVotedInActiveVote && (
              <button onClick={() => setVotingOnLeader(activeVote.id)}
                className="text-left bg-card hover:bg-action/5 border border-warning/30 hover:border-action/30 rounded-lg px-4 py-3 transition-colors">
                <span className="font-body text-body-sm text-text-primary font-medium block">
                  {activeVote.phase === 'removal' ? 'Vote: Remove Head of State' : 'Vote: Elect New Leader'}
                </span>
                <span className="font-body text-caption text-text-secondary">
                  {leaderVoteCountdown !== null && `${Math.floor(leaderVoteCountdown/60)}:${String(Math.floor(leaderVoteCountdown%60)).padStart(2,'0')} remaining — `}
                  Click to vote
                </span>
              </button>
            )}
            {nominationsClosed && activeNominationEvent && (
              <button onClick={() => setShowElectionPanel('nominate')}
                className="text-left bg-card border border-border rounded-lg px-4 py-3 transition-colors hover:bg-base">
                <span className="font-body text-body-sm text-text-primary font-medium block">
                  Nominations Closed — {activeNominationEvent.subtype === 'presidential' ? 'Presidential' : 'Mid-Term'}
                </span>
                <span className="font-body text-caption text-text-secondary">
                  {electionNominations.filter(n => n.election_type === activeNominationEvent.subtype).length} candidates — Election R{activeNominationEvent.round}
                </span>
              </button>
            )}
            {!nominationsClosed && showNomination && activeNominationEvent && (
              <button onClick={() => setShowElectionPanel('nominate')}
                className="text-left bg-card hover:bg-action/5 border-2 border-action/40 hover:border-action/60 rounded-lg px-4 py-3 transition-colors">
                <span className="font-body text-body-sm text-action font-bold block">
                  Columbia Elections — Nominations Open
                </span>
                <span className="font-body text-caption text-text-secondary">
                  {activeNominationEvent.subtype === 'presidential' ? 'Presidential' : 'Mid-Term'} — Click to nominate
                </span>
              </button>
            )}
            {!nominationsClosed && isNominated && activeNominationEvent && (
              <button onClick={() => setShowElectionPanel('nominate')}
                className="text-left bg-success/5 border border-success/30 rounded-lg px-4 py-3 transition-colors hover:bg-success/10">
                <span className="font-body text-body-sm text-success font-medium block">
                  You are nominated — {activeNominationEvent.subtype === 'presidential' ? 'Presidential' : 'Mid-Term'}
                </span>
                <span className="font-body text-caption text-text-secondary">Click to view or withdraw</span>
              </button>
            )}
            {showElectionVote && activeElectionEvent && (
              <button onClick={() => setShowElectionPanel('vote')}
                className="text-left bg-card hover:bg-action/5 border-2 border-action/40 hover:border-action/60 rounded-lg px-4 py-3 transition-colors">
                <span className="font-body text-body-sm text-action font-bold block">
                  Columbia Elections — Cast Your Vote
                </span>
                <span className="font-body text-caption text-text-secondary">
                  {activeElectionEvent.subtype === 'presidential' ? 'Presidential' : 'Mid-Term'} — {electionCandidates.length} candidate{electionCandidates.length !== 1 ? 's' : ''}
                </span>
              </button>
            )}
            {electionResolved && activeElectionEvent && (
              <button onClick={() => setShowElectionPanel('results')}
                className="text-left bg-success/5 border border-success/30 rounded-lg px-4 py-3 transition-colors hover:bg-success/10">
                <span className="font-body text-body-sm text-success font-medium block">
                  Election Results — {activeElectionEvent.subtype === 'presidential' ? 'Presidential' : 'Mid-Term'}
                </span>
                <span className="font-body text-caption text-text-secondary">
                  {electionResolved.winner_role_id ? `Winner: ${electionResolved.winner_role_id}` : 'No majority'} — Click to view
                </span>
              </button>
            )}
            {pendingTxns.map(txn=>
              <button key={txn.id} onClick={()=>setReviewTxn(txn.id)}
                className="text-left bg-card hover:bg-action/5 border border-warning/30 hover:border-action/30 rounded-lg px-4 py-3 transition-colors">
                <span className="font-body text-body-sm text-text-primary font-medium block">Transaction from {txn.proposer}</span>
                <span className="font-body text-caption text-text-secondary">Click to review</span>
              </button>
            )}
            {pendingAgreements.map(agr=>
              <button key={agr.id} onClick={()=>setReviewAgr(agr.id)}
                className="text-left bg-card hover:bg-action/5 border border-action/30 hover:border-action/50 rounded-lg px-4 py-3 transition-colors">
                <span className="font-body text-body-sm text-text-primary font-medium block capitalize">{agr.agreement_type.replace('_',' ')}</span>
                <span className="font-body text-caption text-text-secondary block">"{agr.agreement_name}" — by {agr.proposer_country_code}</span>
                <span className="font-body text-caption text-action mt-1 block">Click to review</span>
              </button>
            )}
            {/* Meeting invitations */}
            {myMeetingInvitations.map(inv => (
              <div key={inv.id} className="bg-card border border-action/30 rounded-lg px-4 py-3">
                <div className="font-body text-body-sm text-text-primary font-medium">
                  {inv.invitation_type === 'one_on_one'
                    ? `Meeting request from ${inv.inviter_role_id}`
                    : `${inv.org_name || inv.org_id} meeting`}
                </div>
                {inv.message && <p className="font-body text-caption text-text-secondary mt-0.5">{inv.message}</p>}
                {inv.theme && <p className="font-body text-caption text-text-secondary mt-0.5">Theme: {inv.theme}</p>}
                <div className="flex gap-2 mt-2">
                  <button onClick={() => handleMeetingResponse(inv.id, 'accept', '')} disabled={meetingSubmitting}
                    className="font-body text-caption font-medium bg-success/10 text-success px-3 py-1 rounded hover:bg-success/20 disabled:opacity-50 transition-colors">
                    Accept
                  </button>
                  <button onClick={() => handleMeetingResponse(inv.id, 'reject', '')} disabled={meetingSubmitting}
                    className="font-body text-caption font-medium bg-danger/10 text-danger px-3 py-1 rounded hover:bg-danger/20 disabled:opacity-50 transition-colors">
                    Decline
                  </button>
                  <button onClick={() => handleMeetingResponse(inv.id, 'later', '')} disabled={meetingSubmitting}
                    className="font-body text-caption font-medium bg-warning/10 text-warning px-3 py-1 rounded hover:bg-warning/20 disabled:opacity-50 transition-colors">
                    Not now
                  </button>
                </div>
              </div>
            ))}
          </div>
        }
      </div>

      {/* Active Meetings — chat buttons */}
      {activeMeetings.length > 0 && (
        <div className="bg-card border border-action/20 rounded-lg p-4">
          <h3 className="font-heading text-caption text-text-secondary uppercase tracking-wider mb-3">Active Meetings</h3>
          <div className="grid grid-cols-2 lg:grid-cols-3 gap-2">
            {activeMeetings.map(m => {
              const isA = m.participant_a_role_id === roleId
              const otherRole = isA ? m.participant_b_role_id : m.participant_a_role_id
              const otherCountry = isA ? m.participant_b_country : m.participant_a_country
              return (
                <div key={m.id} className="relative bg-base hover:bg-action/5 border border-action/30 hover:border-action/50 rounded-lg px-4 py-3 transition-colors group">
                  <button onClick={() => onOpenChat?.(m.id)} className="text-left w-full">
                    <span className="font-body text-body-sm text-text-primary group-hover:text-action block">
                      {otherRole}
                    </span>
                    <span className="font-body text-caption text-text-secondary block">
                      {otherCountry.toUpperCase()}
                    </span>
                    <span className="font-body text-caption text-action/60 group-hover:text-action mt-0.5 block">
                      Open Chat
                    </span>
                  </button>
                  <button
                    onClick={async (e) => {
                      e.stopPropagation()
                      try {
                        await endMeeting(simId, m.id, roleId)
                        setActiveMeetings(prev => prev.filter(x => x.id !== m.id))
                      } catch { /* ignore */ }
                    }}
                    className="absolute top-2 right-2 text-text-secondary/40 hover:text-danger p-1 transition-colors"
                    title="End meeting"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M18 6 6 18M6 6l12 12"/>
                    </svg>
                  </button>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {CATS.map(cat=>{
        const ATTACK_ACTIONS = ['ground_attack','air_strike','naval_combat','naval_bombardment','launch_missile_conventional']
        const acts=cat.actions.filter(a=>{
          // "Attack" is a virtual action — available if role has any combat action
          if (a.id === 'attack') return ATTACK_ACTIONS.some(x=>avail.has(x))
          if (!avail.has(a.id)) return false
          // Phase-restricted actions only show in their phase
          const restrictedPhase = PHASE_RESTRICTED[a.id]
          if (restrictedPhase && currentPhase !== restrictedPhase) return false
          return true
        })
        if(!acts.length) return null
        return <div key={cat.key} className="bg-card border border-border rounded-lg p-4">
          <h3 className="font-heading text-caption text-text-secondary uppercase tracking-wider mb-3">{cat.label}</h3>
          <div className="grid grid-cols-2 lg:grid-cols-3 gap-2">
            {acts.map(a=><button key={a.id} onClick={()=>onSelectAction(a.id)} className="text-left bg-base hover:bg-action/5 border border-border hover:border-action/30 rounded-lg px-4 py-3 transition-colors group">
              <span className="font-body text-body-sm text-text-primary group-hover:text-action">{a.label}</span>
            </button>)}
          </div>
        </div>
      })}
    </div>
  )
}

/* ── Tab: Confidential ─────────────────────────────────────────────────── */

function TabConf({role,artefacts,objectives,personalRels,orgMemberships,onRead}:{
  role:RoleData; artefacts:Artefact[]; objectives:string[]
  personalRels:{other_role:string;type:string;notes:string}[]
  orgMemberships:{org_id:string;role_in_org:string;has_veto:boolean}[]
  onRead:(id:string)=>void
}) {
  const [open,setOpen]=useState<string|null>(null)
  const pRelColor=(t:string)=>({ally:'text-success',patron:'text-action',reports_to:'text-text-secondary',rival:'text-warning',enemy:'text-danger',mentor:'text-accent'}[t]??'text-text-secondary')

  return (
    <div className="space-y-6">
      {/* Confidential Brief */}
      {role.confidential_brief&&<div className="bg-card border border-border rounded-lg p-6">
        <h3 className="font-heading text-h3 text-text-primary mb-3">Confidential Brief</h3>
        <p className="font-body text-body-sm text-text-primary leading-relaxed whitespace-pre-wrap">{role.confidential_brief}</p>
      </div>}

      {/* Objectives */}
      {objectives.length>0&&<div className="bg-card border border-border rounded-lg p-6">
        <h3 className="font-heading text-h3 text-text-primary mb-3">Your Objectives</h3>
        <ul className="space-y-2">
          {objectives.map((obj,i)=><li key={i} className="flex items-start gap-2">
            <span className="font-data text-caption text-action mt-0.5">{i+1}.</span>
            <span className="font-body text-body-sm text-text-primary">{obj}</span>
          </li>)}
        </ul>
      </div>}

      {/* Personal Relationships */}
      {personalRels.length>0&&<div className="bg-card border border-border rounded-lg p-6">
        <h3 className="font-heading text-h3 text-text-primary mb-3">Personal Relationships</h3>
        <div className="space-y-2">
          {personalRels.map((r,i)=>
            <div key={i} className="flex items-center gap-3 bg-base rounded px-3 py-2">
              <span className="font-body text-body-sm text-text-primary font-medium w-28">{r.other_role}</span>
              <span className={`font-body text-caption font-medium ${pRelColor(r.type)}`}>{r.type}</span>
              {r.notes&&<span className="font-body text-caption text-text-secondary">— {r.notes}</span>}
            </div>
          )}
        </div>
      </div>}

      {/* Organization Memberships */}
      {orgMemberships.length>0&&<div className="bg-card border border-border rounded-lg p-6">
        <h3 className="font-heading text-h3 text-text-primary mb-3">Organization Memberships</h3>
        <div className="space-y-2">
          {orgMemberships.map(m=><div key={`${m.org_id}_${m.role_in_org}`} className="flex items-center gap-3 bg-base rounded px-3 py-2">
            <span className="font-body text-body-sm text-text-primary font-medium">{m.org_id.replace(/_/g,' ')}</span>
            <span className="font-body text-caption text-text-secondary">{m.role_in_org}</span>
            {m.has_veto&&<span className="font-body text-caption text-danger font-medium">VETO</span>}
          </div>)}
        </div>
      </div>}

      {/* Intelligence & Documents */}
      {artefacts.length>0&&<div className="space-y-3">
        <h3 className="font-heading text-h3 text-text-primary">Intelligence & Documents</h3>
        {artefacts.map(art=><div key={art.id} className="bg-card border border-border rounded-lg overflow-hidden">
          <button onClick={()=>{setOpen(open===art.id?null:art.id);if(!art.is_read)onRead(art.id)}}
            className="w-full text-left px-5 py-3 flex items-center justify-between hover:bg-base/50 transition-colors">
            <div className="flex items-center gap-3">
              {!art.is_read&&<span className="w-2 h-2 bg-danger rounded-full shrink-0"/>}
              <div>
                <span className="font-body text-body-sm text-text-primary font-medium">{art.title}</span>
                {art.from_entity&&<span className="font-body text-caption text-text-secondary ml-2">— {art.from_entity}</span>}
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span className="font-data text-caption bg-danger/10 text-danger px-2 py-0.5 rounded">{art.classification}</span>
              <span className="text-text-secondary">{open===art.id?'▲':'▼'}</span>
            </div>
          </button>
          {open===art.id&&art.content_html&&<div className="border-t border-border p-4">
            <ArtefactRenderer
              type={art.artefact_type}
              title={art.title}
              subtitle={art.subtitle}
              classification={art.classification}
              from_entity={art.from_entity}
              date_label={art.date_label}
              content_html={art.content_html}
            />
          </div>}
        </div>)}
      </div>}
    </div>
  )
}

/* ── Tab: Country ──────────────────────────────────────────────────────── */

function TabCountry({country,fullCountry,sanctions,tariffs,relationships,orgMemberships,simId}:{
  country:CountryData; fullCountry:Record<string,unknown>|null
  sanctions:{imposer:string;target:string;level:number}[]
  tariffs:{imposer:string;target:string;level:number}[]
  relationships:{to_country_code:string;relationship:string;status:string}[]
  orgMemberships:{org_id:string;role_in_org:string;has_veto:boolean}[]
  simId:string
}) {
  const fc = fullCountry ?? {}
  const cc = country.id
  const [section,setSection]=useState<'overview'|'military'|'trade'|'diplomacy'>('overview')
  const [basingWeGrant,setBasingWeGrant]=useState<string[]>([])
  const [basingWeReceive,setBasingWeReceive]=useState<string[]>([])

  useEffect(()=>{
    supabase.from('relationships').select('from_country_code,to_country_code,basing_rights_a_to_b,basing_rights_b_to_a')
      .eq('sim_run_id',simId)
      .or(`from_country_code.eq.${cc},to_country_code.eq.${cc}`)
      .then(({data})=>{
        const granted:string[]=[], received:string[]=[]
        ;(data??[]).forEach((r:Record<string,unknown>)=>{
          if(r.from_country_code===cc && r.basing_rights_a_to_b) granted.push(r.to_country_code as string)
          if(r.to_country_code===cc && r.basing_rights_b_to_a) granted.push(r.from_country_code as string)
          if(r.from_country_code===cc && r.basing_rights_b_to_a) received.push(r.to_country_code as string)
          if(r.to_country_code===cc && r.basing_rights_a_to_b) received.push(r.from_country_code as string)
        })
        setBasingWeGrant([...new Set(granted)])
        setBasingWeReceive([...new Set(received)])
      })
  },[simId,cc])
  const relColor=(r:string)=>({alliance:'text-success',economic_partnership:'text-action',neutral:'text-text-secondary',hostile:'text-warning',at_war:'text-danger'}[r]??'text-text-secondary')
  const relLabel=(r:string)=>({alliance:'Allied',economic_partnership:'Partnership',neutral:'Neutral',hostile:'Hostile',at_war:'AT WAR'}[r]??r)
  const sanctionsOn = sanctions.filter(s=>s.target===cc)
  const sanctionsBy = sanctions.filter(s=>s.imposer===cc)
  const tariffsOn = tariffs.filter(t=>t.target===cc)
  const tariffsBy = tariffs.filter(t=>t.imposer===cc)

  const [countryRolesTab, setCountryRolesTab] = useState<{id:string;character_name:string;position_type:string;positions?:string[];title:string;status:string}[]>([])
  useEffect(()=>{
    supabase.from('roles').select('id,character_name,position_type,positions,title,status')
      .eq('sim_run_id',simId).eq('country_code',cc).eq('status','active')
      .then(({data})=>{ if(data) setCountryRolesTab(data) })
  },[simId,cc])

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-6 h-6 rounded" style={{backgroundColor:country.color_ui??'#4A5568'}}/>
          <h2 className="font-heading text-h2 text-text-primary">{country.sim_name}</h2>
          <span className="font-body text-caption text-text-secondary">{String(fc.regime_type??'')} · {String(fc.team_type??'')}</span>
        </div>
        <div className="flex gap-1">
          {(['overview','military','trade','diplomacy'] as const).map(v=>
            <button key={v} onClick={()=>setSection(v)}
              className={`font-body text-caption px-3 py-1 rounded transition-colors ${section===v?'bg-action/10 text-action font-medium':'text-text-secondary hover:text-text-primary'}`}>
              {v==='overview'?'Economy':v==='military'?'Military':v==='trade'?'Trade & Sanctions':'Diplomacy'}
            </button>
          )}
        </div>
      </div>

      {/* Country brief */}
      {fc.country_brief&&<div className="bg-card border border-border rounded-lg p-4">
        <p className="font-body text-body-sm text-text-primary leading-relaxed">{String(fc.country_brief)}</p>
      </div>}

      {/* Leadership & Roles */}
      {countryRolesTab.length > 0 && (
        <div className="bg-card border border-border rounded-lg divide-y divide-border">
          {countryRolesTab.map(r => {
            const pos = displayPositions(r as RoleData)
            const isHos = r.positions?.includes('head_of_state') || r.position_type === 'head_of_state'
            return (
              <div key={r.id} className="flex items-center gap-3 px-4 py-2.5">
                <span className={`font-body text-body-sm text-text-primary font-medium w-28 shrink-0 ${isHos ? 'text-warning' : ''}`}>
                  {r.character_name}
                </span>
                <span className={`font-body text-caption px-1.5 py-0.5 rounded ${
                  isHos ? 'bg-warning/10 text-warning' :
                  (r.positions?.includes('military') || r.position_type === 'military_chief') ? 'bg-danger/10 text-danger' :
                  (r.positions?.includes('economy') || r.position_type === 'economy_officer') ? 'bg-accent/10 text-accent' :
                  (r.positions?.includes('diplomat') || r.position_type === 'diplomat') ? 'bg-action/10 text-action' :
                  (r.positions?.includes('security') || r.position_type === 'security') ? 'bg-text-secondary/10 text-text-secondary' :
                  'bg-text-secondary/5 text-text-secondary/60'
                }`}>
                  {pos || 'Citizen'}
                </span>
                {r.title && <span className="font-body text-caption text-text-secondary ml-auto">{r.title}</span>}
              </div>
            )
          })}
        </div>
      )}

      {section==='overview'&&<>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {[
            {l:'GDP',v:`$${country.gdp.toFixed(1)}B`},
            {l:'Growth',v:`${Number(fc.gdp_growth_base??0).toFixed(1)}%`},
            {l:'Stability',v:`${country.stability.toFixed(1)}/10`},
            {l:'Inflation',v:`${country.inflation.toFixed(1)}%`},
            {l:'Treasury',v:`$${country.treasury.toFixed(1)}B`},
            {l:'Debt',v:`${(country.debt_burden*100).toFixed(0)}%`},
            {l:'Tax Rate',v:`${(Number(fc.tax_rate??0)*100).toFixed(0)}%`},
            {l:'Trade Balance',v:`$${Number(fc.trade_balance??0).toFixed(1)}B`},
          ].map(s=><div key={s.l} className="bg-card border border-border rounded-lg p-3">
            <div className="font-body text-caption text-text-secondary uppercase tracking-wider mb-0.5">{s.l}</div>
            <div className="font-data text-data text-text-primary">{s.v}</div>
          </div>)}
        </div>
        <div className="bg-card border border-border rounded-lg p-4">
          <h3 className="font-heading text-caption text-text-secondary uppercase tracking-wider mb-2">Economic Sectors</h3>
          <div className="flex gap-4">
            {[{l:'Resources',v:fc.sector_resources},{l:'Industry',v:fc.sector_industry},{l:'Services',v:fc.sector_services},{l:'Technology',v:fc.sector_technology}].map(s=>
              <div key={s.l}>
                <div className="font-body text-caption text-text-secondary">{s.l}</div>
                <div className="font-data text-data text-text-primary">{String(s.v??0)}%</div>
              </div>
            )}
          </div>
        </div>
        <div className="bg-card border border-border rounded-lg p-4">
          <h3 className="font-heading text-caption text-text-secondary uppercase tracking-wider mb-2">Technology</h3>
          <div className="flex gap-6">
            <div>
              <span className="font-body text-caption text-text-secondary">Nuclear: </span>
              <span className={`font-data text-data ${country.nuclear_level>=3?'text-danger font-bold':country.nuclear_level>=1?'text-warning':'text-text-secondary'}`}>
                L{country.nuclear_level}{country.nuclear_confirmed?' (confirmed)':country.nuclear_level>0?' (unconfirmed)':''}
              </span>
              {Number(fc.nuclear_rd_progress??0)>0&&<span className="font-body text-caption text-text-secondary ml-1">R&D: {(Number(fc.nuclear_rd_progress)*100).toFixed(0)}%</span>}
            </div>
            <div>
              <span className="font-body text-caption text-text-secondary">AI: </span>
              <span className={`font-data text-data ${country.ai_level>=4?'text-accent font-bold':country.ai_level>=1?'text-accent':'text-text-secondary'}`}>
                L{country.ai_level}
              </span>
              {Number(fc.ai_rd_progress??0)>0&&<span className="font-body text-caption text-text-secondary ml-1">R&D: {(Number(fc.ai_rd_progress)*100).toFixed(0)}%</span>}
            </div>
          </div>
        </div>
      </>}

      {section==='military'&&<>
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
          {[
            {l:'Ground',v:country.mil_ground},{l:'Naval',v:country.mil_naval},
            {l:'Tactical Air',v:country.mil_tactical_air},{l:'Strategic Missiles',v:country.mil_strategic_missiles},
            {l:'Air Defense',v:country.mil_air_defense},
          ].map(s=><div key={s.l} className="bg-card border border-border rounded-lg p-3">
            <div className="font-body text-caption text-text-secondary uppercase tracking-wider mb-0.5">{s.l}</div>
            <div className="font-data text-data-lg text-text-primary">{s.v}</div>
          </div>)}
        </div>
        <div className="bg-card border border-border rounded-lg p-4">
          <h3 className="font-heading text-caption text-text-secondary uppercase tracking-wider mb-2">Production</h3>
          <div className="grid grid-cols-3 gap-4 font-body text-caption">
            <div><span className="text-text-secondary">Ground:</span> <span className="text-text-primary">cap {String(fc.prod_cap_ground??0)}/rd, cost ${String(fc.prod_cost_ground??0)}</span></div>
            <div><span className="text-text-secondary">Naval:</span> <span className="text-text-primary">cap {String(fc.prod_cap_naval??0)}/rd, cost ${String(fc.prod_cost_naval??0)}</span></div>
            <div><span className="text-text-secondary">Air:</span> <span className="text-text-primary">cap {String(fc.prod_cap_tactical??0)}/rd, cost ${String(fc.prod_cost_tactical??0)}</span></div>
          </div>
          <div className="mt-2 font-body text-caption text-text-secondary">
            Maintenance: ${String(fc.maintenance_per_unit??0)}/unit · Mobilization pool: {String(fc.mobilization_pool??0)}
          </div>
        </div>
        {(basingWeGrant.length > 0 || basingWeReceive.length > 0) && (
          <div className="bg-card border border-border rounded-lg p-4">
            <h3 className="font-heading text-caption text-text-secondary uppercase tracking-wider mb-2">Basing Rights</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <span className="font-body text-caption text-text-secondary block mb-1">We grant access to:</span>
                {basingWeGrant.length > 0
                  ? basingWeGrant.map(c=><div key={c} className="font-body text-body-sm text-text-primary">{c}</div>)
                  : <span className="font-body text-caption text-text-secondary/50">None</span>}
              </div>
              <div>
                <span className="font-body text-caption text-text-secondary block mb-1">We have access to:</span>
                {basingWeReceive.length > 0
                  ? basingWeReceive.map(c=><div key={c} className="font-body text-body-sm text-text-primary">{c}</div>)
                  : <span className="font-body text-caption text-text-secondary/50">None</span>}
              </div>
            </div>
          </div>
        )}
      </>}

      {section==='trade'&&<>
        {sanctionsOn.length>0&&<div className="bg-card border border-danger/20 rounded-lg p-4">
          <h3 className="font-heading text-caption text-danger uppercase tracking-wider mb-2">Sanctions Against Us</h3>
          <div className="space-y-1">
            {sanctionsOn.map((s,i)=><div key={i} className="flex items-center gap-2 font-body text-body-sm">
              <span className="text-text-primary">{s.imposer}</span>
              <span className="text-danger font-data">Level {s.level}</span>
            </div>)}
          </div>
        </div>}
        {sanctionsBy.length>0&&<div className="bg-card border border-border rounded-lg p-4">
          <h3 className="font-heading text-caption text-text-secondary uppercase tracking-wider mb-2">Sanctions We Impose</h3>
          <div className="space-y-1">
            {sanctionsBy.map((s,i)=><div key={i} className="flex items-center gap-2 font-body text-body-sm">
              <span className="text-text-primary">{s.target}</span>
              <span className="font-data text-warning">Level {s.level}</span>
            </div>)}
          </div>
        </div>}
        {tariffsOn.length>0&&<div className="bg-card border border-warning/20 rounded-lg p-4">
          <h3 className="font-heading text-caption text-warning uppercase tracking-wider mb-2">Tariffs Against Us</h3>
          <div className="space-y-1">
            {tariffsOn.map((t,i)=><div key={i} className="flex items-center gap-2 font-body text-body-sm">
              <span className="text-text-primary">{t.imposer}</span>
              <span className="font-data text-warning">Level {t.level}</span>
            </div>)}
          </div>
        </div>}
        {tariffsBy.length>0&&<div className="bg-card border border-border rounded-lg p-4">
          <h3 className="font-heading text-caption text-text-secondary uppercase tracking-wider mb-2">Tariffs We Impose</h3>
          <div className="space-y-1">
            {tariffsBy.map((t,i)=><div key={i} className="flex items-center gap-2 font-body text-body-sm">
              <span className="text-text-primary">{t.target}</span>
              <span className="font-data text-text-secondary">Level {t.level}</span>
            </div>)}
          </div>
        </div>}
        {sanctionsOn.length===0&&sanctionsBy.length===0&&tariffsOn.length===0&&tariffsBy.length===0&&
          <p className="font-body text-body-sm text-text-secondary">No active sanctions or tariffs.</p>
        }
      </>}

      {section==='diplomacy'&&<>
        {/* Country relationships */}
        <div className="bg-card border border-border rounded-lg p-4">
          <h3 className="font-heading text-caption text-text-secondary uppercase tracking-wider mb-3">Relationships</h3>
          <div className="grid grid-cols-2 lg:grid-cols-3 gap-2">
            {relationships.filter(r=>r.relationship!=='neutral').map(r=>
              <div key={r.to_country_code} className="flex items-center gap-2 bg-base rounded px-3 py-2">
                <span className="font-body text-body-sm text-text-primary">{r.to_country_code}</span>
                <span className={`font-body text-caption font-medium ${relColor(r.relationship)}`}>{relLabel(r.relationship)}</span>
              </div>
            )}
          </div>
          {relationships.filter(r=>r.relationship==='neutral').length>0&&<div className="mt-2">
            <span className="font-body text-caption text-text-secondary">
              Neutral: {relationships.filter(r=>r.relationship==='neutral').map(r=>r.to_country_code).join(', ')}
            </span>
          </div>}
        </div>

        {/* Organization memberships */}
        {orgMemberships.length>0&&<div className="bg-card border border-border rounded-lg p-4">
          <h3 className="font-heading text-caption text-text-secondary uppercase tracking-wider mb-3">Organization Memberships</h3>
          <div className="space-y-2">
            {orgMemberships.map(m=><div key={`${m.org_id}_${m.role_in_org}`} className="flex items-center gap-3 bg-base rounded px-3 py-2">
              <span className="font-body text-body-sm text-text-primary font-medium">{m.org_id.replace(/_/g,' ')}</span>
              <span className="font-body text-caption text-text-secondary">{m.role_in_org}</span>
              {m.has_veto&&<span className="font-body text-caption text-danger font-medium">VETO</span>}
            </div>)}
          </div>
        </div>}
      </>}
    </div>
  )
}

/* ── Tab: World ────────────────────────────────────────────────────────── */

interface WorldRole {
  id: string; character_name: string; country_code: string; position_type: string
  title: string; public_bio: string; is_ai_operated: boolean
}

interface CountryBrief {
  id: string; public_bio: string
}


/* ── Tab: World ────────────────────────────────────────────────────────── */

function TabWorld({simId,round}:{simId:string;round:number}) {
  const [countries,setCountries]=useState<CountryData[]>([])
  const [relationships,setRelationships]=useState<{from_country_code:string;to_country_code:string;relationship:string}[]>([])
  const [worldState,setWorldState]=useState<{oil_price:number;global_trade_volume_index:number;dollar_credibility:number}|null>(null)
  const [roles,setRoles]=useState<WorldRole[]>([])
  const [countryBriefs,setCountryBriefs]=useState<Record<string,string>>({})
  const [view,setView]=useState<'overview'|'military'|'relationships'|'countries'>('overview')
  const [expandedCountry,setExpandedCountry]=useState<string|null>(null)
  const [expandedRole,setExpandedRole]=useState<string|null>(null)

  useEffect(()=>{
    supabase.from('countries')
      .select('id,sim_name,color_ui,gdp,stability,inflation,treasury,mil_ground,mil_naval,mil_tactical_air,mil_strategic_missiles,mil_air_defense,nuclear_level,nuclear_confirmed,ai_level,debt_burden')
      .eq('sim_run_id',simId).order('gdp',{ascending:false})
      .then(({data})=>setCountries((data??[]) as CountryData[]))
    supabase.from('relationships')
      .select('from_country_code,to_country_code,relationship')
      .eq('sim_run_id',simId)
      .then(({data})=>setRelationships((data??[]) as typeof relationships))
    supabase.from('world_state')
      .select('oil_price,global_trade_volume_index,dollar_credibility')
      .eq('sim_run_id',simId).order('round_num',{ascending:false}).limit(1)
      .then(({data})=>{if(data?.[0]) setWorldState(data[0])})
    supabase.from('roles')
      .select('id,character_name,country_code,position_type,title,public_bio,is_ai_operated')
      .eq('sim_run_id',simId).eq('status','active').order('country_code,position_type')
      .then(({data})=>setRoles((data??[]) as WorldRole[]))
    supabase.from('countries')
      .select('id,country_brief')
      .eq('sim_run_id',simId)
      .then(({data})=>{
        const briefs:Record<string,string>={}
        ;(data??[]).forEach((c:{id:string;country_brief:string})=>{if(c.country_brief)briefs[c.id]=c.country_brief})
        setCountryBriefs(briefs)
      })
  },[simId])

  const milTotal=(c:CountryData)=>c.mil_ground+c.mil_naval+c.mil_tactical_air+c.mil_strategic_missiles+c.mil_air_defense
  const relColor=(r:string)=>({alliance:'text-success',economic_partnership:'text-action',neutral:'text-text-secondary',hostile:'text-warning',at_war:'text-danger'}[r]??'text-text-secondary')
  const relLabel=(r:string)=>({alliance:'Allied',economic_partnership:'Partnership',neutral:'Neutral',hostile:'Hostile',at_war:'AT WAR'}[r]??r)

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="font-heading text-h2 text-text-primary">World Overview — R{round}</h2>
        <div className="flex gap-1">
          {(['overview','military','relationships','countries'] as const).map(v=>
            <button key={v} onClick={()=>setView(v)}
              className={`font-body text-caption px-3 py-1 rounded transition-colors ${view===v?'bg-action/10 text-action font-medium':'text-text-secondary hover:text-text-primary'}`}>
              {v==='overview'?'Economy':v==='military'?'Military':v==='relationships'?'Relations':'Countries & People'}
            </button>
          )}
        </div>
      </div>

      {/* Global indicators */}
      {worldState&&<div className="grid grid-cols-3 gap-3">
        <div className="bg-card border border-border rounded-lg px-4 py-2">
          <div className="font-body text-caption text-text-secondary">Oil Price</div>
          <div className="font-data text-data-lg text-text-primary">${worldState.oil_price.toFixed(0)}</div>
        </div>
        <div className="bg-card border border-border rounded-lg px-4 py-2">
          <div className="font-body text-caption text-text-secondary">Trade Volume</div>
          <div className="font-data text-data-lg text-text-primary">{worldState.global_trade_volume_index.toFixed(0)}</div>
        </div>
        <div className="bg-card border border-border rounded-lg px-4 py-2">
          <div className="font-body text-caption text-text-secondary">Dollar Index</div>
          <div className="font-data text-data-lg text-text-primary">{worldState.dollar_credibility.toFixed(0)}</div>
        </div>
      </div>}

      {/* Economy view */}
      {view==='overview'&&<div className="bg-card border border-border rounded-lg overflow-hidden">
        <table className="w-full">
          <thead><tr className="border-b border-border bg-base">
            {['Country','GDP','Stability','Inflation','Debt','Nuclear','AI'].map(h=>
              <th key={h} className={`font-body text-caption text-text-secondary uppercase px-3 py-2 ${h==='Country'?'text-left':'text-right'}`}>{h}</th>
            )}
          </tr></thead>
          <tbody>{countries.map(c=>
            <tr key={c.id} className="border-b border-border/50 hover:bg-base/50">
              <td className="px-3 py-2 flex items-center gap-2">
                <div className="w-3 h-3 rounded" style={{backgroundColor:c.color_ui??'#666'}}/>
                <span className="font-body text-body-sm text-text-primary">{c.sim_name}</span>
              </td>
              <td className="text-right font-data text-caption text-text-primary px-3 py-2">{c.gdp.toFixed(0)}B</td>
              <td className="text-right font-data text-caption px-3 py-2">
                <span className={c.stability>=7?'text-success':c.stability>=4?'text-warning':'text-danger'}>{c.stability.toFixed(1)}</span>
              </td>
              <td className="text-right font-data text-caption text-text-primary px-3 py-2">{c.inflation.toFixed(1)}%</td>
              <td className="text-right font-data text-caption text-text-secondary px-3 py-2">{(c.debt_burden*100).toFixed(0)}%</td>
              <td className="text-right font-data text-caption px-3 py-2">
                {c.nuclear_level>0?<span className={c.nuclear_level>=3?'text-danger font-bold':'text-warning'}>L{c.nuclear_level}{c.nuclear_confirmed?'':'?'}</span>:<span className="text-text-secondary/30">—</span>}
              </td>
              <td className="text-right font-data text-caption px-3 py-2">
                {c.ai_level>0?<span className="text-accent">L{c.ai_level}</span>:<span className="text-text-secondary/30">—</span>}
              </td>
            </tr>
          )}</tbody>
        </table>
      </div>}

      {/* Military view */}
      {view==='military'&&<div className="bg-card border border-border rounded-lg overflow-hidden">
        <table className="w-full">
          <thead><tr className="border-b border-border bg-base">
            {['Country','Ground','Naval','Air','Missiles','AD','Total'].map(h=>
              <th key={h} className={`font-body text-caption text-text-secondary uppercase px-3 py-2 ${h==='Country'?'text-left':'text-right'}`}>{h}</th>
            )}
          </tr></thead>
          <tbody>{[...countries].sort((a,b)=>milTotal(b)-milTotal(a)).map(c=>
            <tr key={c.id} className="border-b border-border/50 hover:bg-base/50">
              <td className="px-3 py-2 flex items-center gap-2">
                <div className="w-3 h-3 rounded" style={{backgroundColor:c.color_ui??'#666'}}/>
                <span className="font-body text-body-sm text-text-primary">{c.sim_name}</span>
              </td>
              <td className="text-right font-data text-caption text-text-primary px-3 py-2">{c.mil_ground||'—'}</td>
              <td className="text-right font-data text-caption text-text-primary px-3 py-2">{c.mil_naval||'—'}</td>
              <td className="text-right font-data text-caption text-text-primary px-3 py-2">{c.mil_tactical_air||'—'}</td>
              <td className="text-right font-data text-caption text-text-primary px-3 py-2">{c.mil_strategic_missiles||'—'}</td>
              <td className="text-right font-data text-caption text-text-primary px-3 py-2">{c.mil_air_defense||'—'}</td>
              <td className="text-right font-data text-data font-bold text-text-primary px-3 py-2">{milTotal(c)}</td>
            </tr>
          )}</tbody>
        </table>
      </div>}

      {/* Relationships view */}
      {view==='relationships'&&<div className="bg-card border border-border rounded-lg p-4">
        <div className="space-y-1">
          {countries.slice(0,12).map(c=>{
            const rels=relationships.filter(r=>r.from_country_code===c.id&&r.relationship!=='neutral')
            if(!rels.length) return null
            return <div key={c.id} className="flex items-center gap-2 py-1">
              <div className="w-3 h-3 rounded shrink-0" style={{backgroundColor:c.color_ui??'#666'}}/>
              <span className="font-body text-caption text-text-primary w-24 shrink-0">{c.sim_name}</span>
              <div className="flex flex-wrap gap-1">
                {rels.map((r,i)=>{
                  const target=countries.find(x=>x.id===r.to_country_code)
                  return <span key={i} className={`font-body text-caption ${relColor(r.relationship)}`}>
                    {target?.sim_name??r.to_country_code}({relLabel(r.relationship)})
                  </span>
                })}
              </div>
            </div>
          })}
        </div>
      </div>}

      {/* Countries & People view */}
      {view==='countries'&&<div className="space-y-2">
        {countries.map(c=>{
          const countryRoles=roles.filter(r=>r.country_code===c.id)
          const isExpanded=expandedCountry===c.id
          return <div key={c.id} className="bg-card border border-border rounded-lg overflow-hidden">
            <button onClick={()=>setExpandedCountry(isExpanded?null:c.id)}
              className="w-full text-left px-4 py-3 flex items-center justify-between hover:bg-base/50 transition-colors">
              <div className="flex items-center gap-3">
                <div className="w-4 h-4 rounded" style={{backgroundColor:c.color_ui??'#666'}}/>
                <span className="font-heading text-body-sm text-text-primary font-medium">{c.sim_name}</span>
                <span className="font-body text-caption text-text-secondary">{countryRoles.length} roles</span>
              </div>
              <span className="text-text-secondary text-sm">{isExpanded?'▲':'▼'}</span>
            </button>

            {isExpanded&&<div className="border-t border-border">
              {/* Country brief */}
              {countryBriefs[c.id]&&<div className="px-4 py-3 bg-base/50 border-b border-border">
                <p className="font-body text-body-sm text-text-primary leading-relaxed">{countryBriefs[c.id]}</p>
              </div>}

              {/* Team members */}
              <div className="px-4 py-3 space-y-2">
                {countryRoles.map(role=>{
                  const roleExpanded=expandedRole===role.id
                  return <div key={role.id}>
                    <button onClick={()=>setExpandedRole(roleExpanded?null:role.id)}
                      className="w-full text-left flex items-center gap-3 py-1 hover:bg-base/30 rounded px-2 -mx-2 transition-colors">
                      <span className="font-body text-body-sm text-text-primary font-medium w-28 shrink-0">{role.character_name}</span>
                      <span className={`font-body text-caption px-1.5 py-0.5 rounded ${
                        (role.positions?.includes('head_of_state') || role.position_type==='head_of_state')?'bg-warning/10 text-warning':
                        (role.positions?.includes('military') || role.position_type==='military_chief')?'bg-danger/10 text-danger':
                        (role.positions?.includes('economy') || role.position_type==='economy_officer')?'bg-accent/10 text-accent':
                        (role.positions?.includes('diplomat') || role.position_type==='diplomat')?'bg-action/10 text-action':
                        'bg-text-secondary/10 text-text-secondary'
                      }`}>
                        {displayPositions(role as RoleData)}
                      </span>
                      <span className="font-body text-caption text-text-secondary flex-1">{role.title}</span>
                      {role.is_ai_operated&&<span className="font-body text-caption text-accent/60">AI</span>}
                    </button>
                    {roleExpanded&&role.public_bio&&<div className="ml-2 pl-4 border-l-2 border-border my-2">
                      <p className="font-body text-caption text-text-secondary leading-relaxed">{role.public_bio}</p>
                    </div>}
                  </div>
                })}
              </div>
            </div>}
          </div>
        })}
      </div>}
    </div>
  )
}
