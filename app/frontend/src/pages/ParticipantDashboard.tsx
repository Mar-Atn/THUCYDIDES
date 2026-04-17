/**
 * Participant Dashboard — what human players see during the simulation.
 * Route: /play/:simId
 *
 * Tabs: Actions | Strictly Confidential | Country | World | Global Map
 * Persistent: Header (role + round + timer), Navigator button, Moderator broadcast
 *
 * M6 Sprint 6.1: Shell, tabs, header, data loading
 */

import { useEffect, useState, useCallback, useRef } from 'react'
import { useParams } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { supabase } from '@/lib/supabase'
import { getSimRun, type SimRun } from '@/lib/queries'
import { ArtefactRenderer } from '@/components/ArtefactRenderer'

/* ── Types ─────────────────────────────────────────────────────────────── */

interface RoleData {
  id: string; character_name: string; country_id: string; position_type: string
  title: string; public_bio: string; confidential_brief: string | null
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
    {id:'public_statement',label:'Public Statement'},{id:'meet_freely',label:'Meet Anyone'},{id:'call_org_meeting',label:'Call Org Meeting'},
  ]},
  { key:'military', label:'Military', actions:[
    {id:'ground_attack',label:'Ground Attack'},{id:'air_strike',label:'Air Strike'},{id:'naval_combat',label:'Naval Combat'},
    {id:'naval_bombardment',label:'Naval Bombardment'},{id:'launch_missile_conventional',label:'Missile Launch'},
    {id:'naval_blockade',label:'Naval Blockade'},{id:'move_units',label:'Move Units (inter-round)'},
    {id:'martial_law',label:'Martial Law'},{id:'nuclear_test',label:'Nuclear Test'},
    {id:'nuclear_launch_initiate',label:'Nuclear Launch'},{id:'nuclear_authorize',label:'Authorize Nuclear'},
    {id:'nuclear_intercept',label:'Intercept Missiles'},
  ]},
  { key:'economic', label:'Economic', actions:[
    {id:'set_budget',label:'Set Budget'},{id:'set_tariffs',label:'Set Tariffs'},
    {id:'set_sanctions',label:'Set Sanctions'},{id:'set_opec',label:'Set Cartel Production'},
  ]},
  { key:'intl', label:'International Affairs', actions:[
    {id:'propose_transaction',label:'Propose Transaction'},{id:'accept_transaction',label:'Respond to Transaction'},
    {id:'propose_agreement',label:'Propose Agreement'},{id:'sign_agreement',label:'Sign Agreement'},
    {id:'basing_rights',label:'Basing Rights'},
  ]},
  { key:'covert', label:'Secret Operations', actions:[
    {id:'intelligence',label:'Intelligence'},{id:'covert_operation',label:'Covert Operation'},{id:'assassination',label:'Assassination'},
  ]},
  { key:'political', label:'Political', actions:[
    {id:'reassign_types',label:'Reassign Powers'},{id:'arrest',label:'Arrest'},{id:'change_leader',label:'Change Leader'},
    {id:'self_nominate',label:'Self-Nominate'},{id:'cast_vote',label:'Cast Vote'},
  ]},
]

/* ── Main Component ────────────────────────────────────────────────────── */

export function ParticipantDashboard() {
  const { simId } = useParams<{ simId: string }>()
  const { user, profile } = useAuth()

  // Proxy mode: ?role=sabre allows moderator to view as a specific role
  const urlParams = new URLSearchParams(window.location.search)
  const proxyRoleId = urlParams.get('role')
  const isProxyMode = !!proxyRoleId

  const [simRun, setSimRun] = useState<SimRun | null>(null)
  const [myRole, setMyRole] = useState<RoleData | null>(null)
  const [myCountry, setMyCountry] = useState<CountryData | null>(null)
  const [artefacts, setArtefacts] = useState<Artefact[]>([])
  const [simState, setSimState] = useState<SimState | null>(null)
  const [tab, setTab] = useState<TabId>('actions')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [remaining, setRemaining] = useState<number | null>(null)
  const [broadcast, setBroadcast] = useState<string | null>(null)
  const [roleActions, setRoleActions] = useState<string[]>([])
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const loadData = useCallback(async () => {
    if (!simId || !user) return
    try {
      const run = await getSimRun(simId)
      if (!run) { setError('Simulation not found'); setLoading(false); return }
      setSimRun(run)
      setSimState({ status:run.status, current_round:run.current_round, current_phase:run.current_phase,
        phase_started_at:run.started_at, phase_duration_seconds:run.schedule?.phase_a_minutes?run.schedule.phase_a_minutes*60:3600 })

      // Load role: proxy mode uses role_id, normal mode uses user_id
      const roleQuery = supabase.from('roles')
        .select('id,character_name,country_id,position_type,title,public_bio,confidential_brief')
        .eq('sim_run_id',simId)
      const { data: roles } = proxyRoleId
        ? await roleQuery.eq('id', proxyRoleId).limit(1)
        : await roleQuery.eq('user_id', user.id).limit(1)
      if (roles?.[0]) {
        const role = roles[0] as RoleData; setMyRole(role)
        const { data: c } = await supabase.from('countries')
          .select('id,sim_name,color_ui,gdp,stability,inflation,treasury,mil_ground,mil_naval,mil_tactical_air,mil_strategic_missiles,mil_air_defense,nuclear_level,nuclear_confirmed,ai_level,debt_burden')
          .eq('sim_run_id',simId).eq('id',role.country_id).limit(1)
        if (c?.[0]) setMyCountry(c[0] as CountryData)
        const { data: arts } = await supabase.from('artefacts').select('*')
          .eq('sim_run_id',simId).eq('role_id',role.id).order('round_delivered')
        setArtefacts((arts??[]) as Artefact[])
        const { data: ra } = await supabase.from('role_actions').select('action_id')
          .eq('sim_run_id',simId).eq('role_id',role.id)
        setRoleActions((ra??[]).map((r:{action_id:string})=>r.action_id))
      } else { setTab('world') }
      setError(null)
    } catch(e) { setError(e instanceof Error?e.message:'Failed') }
    finally { setLoading(false) }
  }, [simId, user])

  useEffect(() => { loadData() }, [loadData])

  useEffect(() => {
    if (!simId) return
    const ch = supabase.channel(`part:${simId}`)
      .on('postgres_changes',{event:'UPDATE',schema:'public',table:'sim_runs',filter:`id=eq.${simId}`},(p)=>{
        const r=p.new as Record<string,unknown>
        if(r){setSimRun(prev=>prev?{...prev,...r}as SimRun:prev);setSimState({
          status:(r.status as string)??'setup',current_round:(r.current_round as number)??0,
          current_phase:(r.current_phase as string)??'pre',phase_started_at:(r.phase_started_at as string|null)??null,
          phase_duration_seconds:(r.phase_duration_seconds as number|null)??3600})}
      }).subscribe()
    return ()=>{supabase.removeChannel(ch)}
  }, [simId])

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
    {id:'actions',label:'Actions',off:!hasRole},
    {id:'confidential',label:'Confidential',badge:unread||undefined,off:!hasRole},
    {id:'country',label:'Country',off:!hasRole},
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
                <div className="font-body text-caption text-text-secondary">{myRole!.title} · {myCountry?.sim_name??myRole!.country_id}</div>
              </div>
              <span className="font-body text-caption font-medium px-2 py-0.5 rounded" style={{backgroundColor:`${color}15`,color}}>{POS[myRole!.position_type]??myRole!.position_type}</span>
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
        <button onClick={()=>setBroadcast(null)} className="text-text-secondary hover:text-text-primary">✕</button>
      </div></div>}

      {/* TABS */}
      <nav className="bg-card border-b border-border px-6">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex">
            {tabs.map(t=>(
              <button key={t.id} onClick={()=>!t.off&&setTab(t.id)} disabled={t.off}
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
        {tab==='actions'&&myRole&&<TabActions roleActions={roleActions} currentPhase={simState?.current_phase??'pre'}/>}
        {tab==='confidential'&&myRole&&<TabConf role={myRole} artefacts={artefacts} onRead={id=>{
          supabase.from('artefacts').update({is_read:true}).eq('id',id).then(()=>{
            setArtefacts(p=>p.map(a=>a.id===id?{...a,is_read:true}:a))
          })
        }}/>}
        {tab==='country'&&myCountry&&<TabCountry country={myCountry}/>}
        {tab==='world'&&<TabWorld simId={simId!} round={round}/>}
        {tab==='map'&&<div className="relative" style={{height:'calc(100vh - 180px)'}}>
          <iframe src={`/map/deployments.html?display=clean&sim_run_id=${simId}`} className="absolute inset-0 w-full h-full border-0 rounded-lg" title="Map"/>
        </div>}
      </main>
    </div>
  )
}

/* ── Tab: Actions ──────────────────────────────────────────────────────── */

function TabActions({roleActions, currentPhase}:{roleActions:string[]; currentPhase: string}) {
  const avail = new Set(roleActions)
  return (
    <div className="space-y-4">
      <div className="bg-warning/5 border border-warning/20 rounded-lg p-4">
        <h3 className="font-heading text-h3 text-warning mb-1">Actions Expected Now</h3>
        <p className="font-body text-caption text-text-secondary">No urgent actions at this time.</p>
      </div>
      {CATS.map(cat=>{
        const acts=cat.actions.filter(a=>{
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
            {acts.map(a=><button key={a.id} className="text-left bg-base hover:bg-action/5 border border-border hover:border-action/30 rounded-lg px-4 py-3 transition-colors group">
              <span className="font-body text-body-sm text-text-primary group-hover:text-action">{a.label}</span>
            </button>)}
          </div>
        </div>
      })}
    </div>
  )
}

/* ── Tab: Confidential ─────────────────────────────────────────────────── */

function TabConf({role,artefacts,onRead}:{role:RoleData;artefacts:Artefact[];onRead:(id:string)=>void}) {
  const [open,setOpen]=useState<string|null>(null)
  return (
    <div className="space-y-6">
      {role.confidential_brief&&<div className="bg-card border border-border rounded-lg p-6">
        <h3 className="font-heading text-h3 text-text-primary mb-3">Confidential Brief</h3>
        <p className="font-body text-body-sm text-text-primary leading-relaxed whitespace-pre-wrap">{role.confidential_brief}</p>
      </div>}
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

function TabCountry({country}:{country:CountryData}) {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="w-6 h-6 rounded" style={{backgroundColor:country.color_ui??'#4A5568'}}/>
        <h2 className="font-heading text-h2 text-text-primary">{country.sim_name}</h2>
      </div>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[{l:'GDP',v:`$${country.gdp.toFixed(1)}B`},{l:'Stability',v:`${country.stability.toFixed(1)}/10`},{l:'Inflation',v:`${country.inflation.toFixed(1)}%`},{l:'Treasury',v:`$${country.treasury.toFixed(1)}B`}].map(s=>
          <div key={s.l} className="bg-card border border-border rounded-lg p-4">
            <div className="font-body text-caption text-text-secondary uppercase tracking-wider mb-1">{s.l}</div>
            <div className="font-data text-data-lg text-text-primary">{s.v}</div>
          </div>
        )}
      </div>
      <p className="font-body text-caption text-text-secondary italic">Full country dashboard — military, economic details, relationships — coming in Sprint 6.4.</p>
    </div>
  )
}

/* ── Tab: World ────────────────────────────────────────────────────────── */

function TabWorld({simId,round}:{simId:string;round:number}) {
  const [countries,setCountries]=useState<CountryData[]>([])
  const [relationships,setRelationships]=useState<{from_country_id:string;to_country_id:string;relationship:string}[]>([])
  const [worldState,setWorldState]=useState<{oil_price:number;global_trade_volume_index:number;dollar_credibility:number}|null>(null)
  const [view,setView]=useState<'overview'|'military'|'relationships'>('overview')

  useEffect(()=>{
    supabase.from('countries')
      .select('id,sim_name,color_ui,gdp,stability,inflation,treasury,mil_ground,mil_naval,mil_tactical_air,mil_strategic_missiles,mil_air_defense,nuclear_level,nuclear_confirmed,ai_level,debt_burden')
      .eq('sim_run_id',simId).order('gdp',{ascending:false})
      .then(({data})=>setCountries((data??[]) as CountryData[]))
    supabase.from('relationships')
      .select('from_country_id,to_country_id,relationship')
      .eq('sim_run_id',simId)
      .then(({data})=>setRelationships((data??[]) as typeof relationships))
    supabase.from('world_state')
      .select('oil_price,global_trade_volume_index,dollar_credibility')
      .eq('sim_run_id',simId).order('round_num',{ascending:false}).limit(1)
      .then(({data})=>{if(data?.[0]) setWorldState(data[0])})
  },[simId])

  const milTotal=(c:CountryData)=>c.mil_ground+c.mil_naval+c.mil_tactical_air+c.mil_strategic_missiles+c.mil_air_defense
  const relColor=(r:string)=>({alliance:'text-success',economic_partnership:'text-action',neutral:'text-text-secondary',hostile:'text-warning',at_war:'text-danger'}[r]??'text-text-secondary')
  const relLabel=(r:string)=>({alliance:'Allied',economic_partnership:'Partnership',neutral:'Neutral',hostile:'Hostile',at_war:'AT WAR'}[r]??r)

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="font-heading text-h2 text-text-primary">World Overview — R{round}</h2>
        <div className="flex gap-1">
          {(['overview','military','relationships'] as const).map(v=>
            <button key={v} onClick={()=>setView(v)}
              className={`font-body text-caption px-3 py-1 rounded transition-colors ${view===v?'bg-action/10 text-action font-medium':'text-text-secondary hover:text-text-primary'}`}>
              {v==='overview'?'Economy':v==='military'?'Military':'Relations'}
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
            const rels=relationships.filter(r=>r.from_country_id===c.id&&r.relationship!=='neutral')
            if(!rels.length) return null
            return <div key={c.id} className="flex items-center gap-2 py-1">
              <div className="w-3 h-3 rounded shrink-0" style={{backgroundColor:c.color_ui??'#666'}}/>
              <span className="font-body text-caption text-text-primary w-24 shrink-0">{c.sim_name}</span>
              <div className="flex flex-wrap gap-1">
                {rels.map((r,i)=>{
                  const target=countries.find(x=>x.id===r.to_country_id)
                  return <span key={i} className={`font-body text-caption ${relColor(r.relationship)}`}>
                    {target?.sim_name??r.to_country_id}({relLabel(r.relationship)})
                  </span>
                })}
              </div>
            </div>
          })}
        </div>
      </div>}
    </div>
  )
}
