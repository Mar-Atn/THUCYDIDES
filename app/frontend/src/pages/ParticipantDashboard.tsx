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
import { getSimRun, submitAction, type SimRun } from '@/lib/queries'
import { ArtefactRenderer } from '@/components/ArtefactRenderer'

/* ── Types ─────────────────────────────────────────────────────────────── */

interface RoleData {
  id: string; character_name: string; country_id: string; position_type: string
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
  const [objectives, setObjectives] = useState<string[]>([])
  const [myRelationships, setMyRelationships] = useState<{to_country_id:string;relationship:string;status:string}[]>([])
  const [myOrgMemberships, setMyOrgMemberships] = useState<{org_id:string;role_in_org:string;has_veto:boolean}[]>([])
  const [personalRels, setPersonalRels] = useState<{other_role:string;type:string;notes:string}[]>([])
  const [activeAction, setActiveAction] = useState<string|null>(null)
  const [mySanctions, setMySanctions] = useState<{imposer:string;target:string;level:number}[]>([])
  const [myTariffs, setMyTariffs] = useState<{imposer:string;target:string;level:number}[]>([])
  const [fullCountry, setFullCountry] = useState<Record<string,unknown>|null>(null)
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
        .select('id,character_name,country_id,position_type,title,public_bio,confidential_brief,objectives,powers')
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

        // Objectives from role
        setObjectives(Array.isArray(role.objectives) ? role.objectives as string[] : [])

        // Relationships for own country
        const { data: rels } = await supabase.from('relationships')
          .select('to_country_id,relationship,status')
          .eq('sim_run_id',simId).eq('from_country_id',role.country_id)
        setMyRelationships((rels??[]) as typeof myRelationships)

        // Org memberships
        const { data: mems } = await supabase.from('org_memberships')
          .select('org_id,role_in_org,has_veto')
          .eq('sim_run_id',simId).eq('country_id',role.country_id)
        setMyOrgMemberships((mems??[]) as typeof myOrgMemberships)

        // Personal role relationships
        const { data: prA } = await supabase.from('role_relationships')
          .select('role_a_id,role_b_id,relationship_type,notes')
          .eq('sim_run_id',simId).eq('role_a_id',role.id)
        const { data: prB } = await supabase.from('role_relationships')
          .select('role_a_id,role_b_id,relationship_type,notes')
          .eq('sim_run_id',simId).eq('role_b_id',role.id)
        const pRels = [
          ...((prA??[]).map((r:{role_a_id:string;role_b_id:string;relationship_type:string;notes:string})=>({other_role:r.role_b_id,type:r.relationship_type,notes:r.notes||''}))),
          ...((prB??[]).map((r:{role_a_id:string;role_b_id:string;relationship_type:string;notes:string})=>({other_role:r.role_a_id,type:r.relationship_type,notes:r.notes||''}))),
        ]
        setPersonalRels(pRels)

        // Sanctions (received + imposed)
        const { data: sr } = await supabase.from('sanctions')
          .select('imposer_country_id,target_country_id,level')
          .eq('sim_run_id',simId).or(`target_country_id.eq.${role.country_id},imposer_country_id.eq.${role.country_id}`)
        const sanctions = (sr??[]).map((s:{imposer_country_id:string;target_country_id:string;level:number})=>({imposer:s.imposer_country_id,target:s.target_country_id,level:s.level}))
        setMySanctions(sanctions)

        // Tariffs (received + imposed)
        const { data: tr } = await supabase.from('tariffs')
          .select('imposer_country_id,target_country_id,level')
          .eq('sim_run_id',simId).or(`target_country_id.eq.${role.country_id},imposer_country_id.eq.${role.country_id}`)
        const tariffs = (tr??[]).map((t:{imposer_country_id:string;target_country_id:string;level:number})=>({imposer:t.imposer_country_id,target:t.target_country_id,level:t.level}))
        setMyTariffs(tariffs)

        // Full country data
        const { data: fc } = await supabase.from('countries').select('*')
          .eq('sim_run_id',simId).eq('id',role.country_id).limit(1)
        if (fc?.[0]) setFullCountry(fc[0])

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
        {tab==='actions'&&myRole&&(
          activeAction
            ? <ActionForm
                actionType={activeAction}
                roleId={myRole.id}
                roleName={myRole.character_name}
                countryId={myRole.country_id}
                simId={simId!}
                onClose={()=>setActiveAction(null)}
                onSubmitted={()=>{setActiveAction(null); loadData()}}
              />
            : <TabActions roleActions={roleActions} currentPhase={simState?.current_phase??'pre'} onSelectAction={setActiveAction}/>
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
    </div>
  )
}

/* ── Tab: Actions ──────────────────────────────────────────────────────── */

function TabActions({roleActions, currentPhase, onSelectAction}:{roleActions:string[]; currentPhase:string; onSelectAction:(id:string)=>void}) {
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
          {orgMemberships.map(m=><div key={m.org_id} className="flex items-center gap-3 bg-base rounded px-3 py-2">
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
  relationships:{to_country_id:string;relationship:string;status:string}[]
  orgMemberships:{org_id:string;role_in_org:string;has_veto:boolean}[]
  simId:string
}) {
  const fc = fullCountry ?? {}
  const cc = country.id
  const [section,setSection]=useState<'overview'|'military'|'trade'|'diplomacy'>('overview')
  const relColor=(r:string)=>({alliance:'text-success',economic_partnership:'text-action',neutral:'text-text-secondary',hostile:'text-warning',at_war:'text-danger'}[r]??'text-text-secondary')
  const relLabel=(r:string)=>({alliance:'Allied',economic_partnership:'Partnership',neutral:'Neutral',hostile:'Hostile',at_war:'AT WAR'}[r]??r)
  const sanctionsOn = sanctions.filter(s=>s.target===cc)
  const sanctionsBy = sanctions.filter(s=>s.imposer===cc)
  const tariffsOn = tariffs.filter(t=>t.target===cc)
  const tariffsBy = tariffs.filter(t=>t.imposer===cc)

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
              <div key={r.to_country_id} className="flex items-center gap-2 bg-base rounded px-3 py-2">
                <span className="font-body text-body-sm text-text-primary">{r.to_country_id}</span>
                <span className={`font-body text-caption font-medium ${relColor(r.relationship)}`}>{relLabel(r.relationship)}</span>
              </div>
            )}
          </div>
          {relationships.filter(r=>r.relationship==='neutral').length>0&&<div className="mt-2">
            <span className="font-body text-caption text-text-secondary">
              Neutral: {relationships.filter(r=>r.relationship==='neutral').map(r=>r.to_country_id).join(', ')}
            </span>
          </div>}
        </div>

        {/* Organization memberships */}
        {orgMemberships.length>0&&<div className="bg-card border border-border rounded-lg p-4">
          <h3 className="font-heading text-caption text-text-secondary uppercase tracking-wider mb-3">Organization Memberships</h3>
          <div className="space-y-2">
            {orgMemberships.map(m=><div key={m.org_id} className="flex items-center gap-3 bg-base rounded px-3 py-2">
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
  id: string; character_name: string; country_id: string; position_type: string
  title: string; public_bio: string; is_ai_operated: boolean
}

interface CountryBrief {
  id: string; public_bio: string
}

/* ── ActionForm — full-screen form for submitting an action ────────────── */

const ACTION_LABELS: Record<string,string> = Object.fromEntries(
  CATS.flatMap(c=>c.actions.map(a=>[a.id,a.label]))
)

function ActionForm({actionType,roleId,roleName,countryId,simId,onClose,onSubmitted}:{
  actionType:string; roleId:string; roleName:string; countryId:string; simId:string
  onClose:()=>void; onSubmitted:()=>void
}) {
  const label = ACTION_LABELS[actionType] ?? actionType

  // Route to specific form or generic placeholder
  if (actionType === 'public_statement') return <PublicStatementForm {...{roleId,roleName,countryId,simId,onClose,onSubmitted}} />

  // Generic "coming soon" for actions not yet wired
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="font-heading text-h2 text-text-primary">{label}</h2>
        <button onClick={onClose} className="font-body text-caption text-text-secondary hover:text-text-primary px-3 py-1 rounded border border-border hover:border-action/30">
          ← Back to Actions
        </button>
      </div>
      <div className="bg-card border border-border rounded-lg p-8 text-center">
        <p className="font-body text-body text-text-secondary">
          Action form for <strong>{label}</strong> — coming in next sprint.
        </p>
      </div>
    </div>
  )
}

/* ── Public Statement Form ─────────────────────────────────────────────── */

function PublicStatementForm({roleId,roleName,countryId,simId,onClose,onSubmitted}:{
  roleId:string; roleName:string; countryId:string; simId:string
  onClose:()=>void; onSubmitted:()=>void
}) {
  const [text, setText] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState<string|null>(null)
  const [error, setError] = useState<string|null>(null)

  const handleSubmit = async () => {
    if (!text.trim()) return
    setSubmitting(true)
    setError(null)
    try {
      const res = await submitAction(simId, 'public_statement', roleId, countryId, { content: text.trim() })
      setResult(res.narrative as string ?? 'Statement published')
      setText('')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to submit')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="font-heading text-h2 text-text-primary">Public Statement</h2>
        <button onClick={onClose} className="font-body text-caption text-text-secondary hover:text-text-primary px-3 py-1 rounded border border-border hover:border-action/30">
          ← Back to Actions
        </button>
      </div>

      <div className="bg-card border border-border rounded-lg p-6 space-y-4">
        <div>
          <label className="font-body text-caption text-text-secondary block mb-2">
            Speaking as <strong className="text-text-primary">{roleName}</strong> ({countryId})
          </label>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Address the world... Your statement will be visible to all participants and appear on the public screen."
            rows={6}
            className="w-full bg-base border border-border rounded-lg px-4 py-3 font-body text-body-sm text-text-primary resize-none focus:border-action/50 focus:outline-none transition-colors"
            disabled={submitting}
          />
          <div className="flex items-center justify-between mt-1">
            <span className="font-body text-caption text-text-secondary">
              {text.length} characters
            </span>
            {text.length > 0 && text.length < 10 && (
              <span className="font-body text-caption text-warning">Minimum 10 characters</span>
            )}
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleSubmit}
            disabled={submitting || text.trim().length < 10}
            className="bg-action text-white font-body text-body-sm font-medium px-6 py-2.5 rounded-lg hover:bg-action/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {submitting ? 'Publishing...' : 'Publish Statement'}
          </button>
          <button
            onClick={onClose}
            className="font-body text-body-sm text-text-secondary hover:text-text-primary px-4 py-2.5"
          >
            Cancel
          </button>
        </div>

        {result && (
          <div className="bg-success/5 border border-success/20 rounded-lg p-4">
            <p className="font-body text-body-sm text-success">Statement published successfully.</p>
            <p className="font-body text-caption text-text-secondary mt-1">{result}</p>
            <button onClick={onSubmitted} className="font-body text-caption text-action hover:underline mt-2">
              ← Return to Actions
            </button>
          </div>
        )}

        {error && (
          <div className="bg-danger/5 border border-danger/20 rounded-lg p-4">
            <p className="font-body text-body-sm text-danger">{error}</p>
          </div>
        )}
      </div>
    </div>
  )
}

/* ── Tab: World ────────────────────────────────────────────────────────── */

function TabWorld({simId,round}:{simId:string;round:number}) {
  const [countries,setCountries]=useState<CountryData[]>([])
  const [relationships,setRelationships]=useState<{from_country_id:string;to_country_id:string;relationship:string}[]>([])
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
      .select('from_country_id,to_country_id,relationship')
      .eq('sim_run_id',simId)
      .then(({data})=>setRelationships((data??[]) as typeof relationships))
    supabase.from('world_state')
      .select('oil_price,global_trade_volume_index,dollar_credibility')
      .eq('sim_run_id',simId).order('round_num',{ascending:false}).limit(1)
      .then(({data})=>{if(data?.[0]) setWorldState(data[0])})
    supabase.from('roles')
      .select('id,character_name,country_id,position_type,title,public_bio,is_ai_operated')
      .eq('sim_run_id',simId).eq('status','active').order('country_id,position_type')
      .then(({data})=>setRoles((data??[]) as WorldRole[]))
    supabase.from('countries')
      .select('id,public_bio')
      .eq('sim_run_id',simId)
      .then(({data})=>{
        const briefs:Record<string,string>={}
        ;(data??[]).forEach((c:{id:string;public_bio:string})=>{if(c.public_bio)briefs[c.id]=c.public_bio})
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

      {/* Countries & People view */}
      {view==='countries'&&<div className="space-y-2">
        {countries.map(c=>{
          const countryRoles=roles.filter(r=>r.country_id===c.id)
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
                        role.position_type==='head_of_state'?'bg-warning/10 text-warning':
                        role.position_type==='military_chief'?'bg-danger/10 text-danger':
                        role.position_type==='economy_officer'?'bg-accent/10 text-accent':
                        role.position_type==='diplomat'?'bg-action/10 text-action':
                        'bg-text-secondary/10 text-text-secondary'
                      }`}>
                        {POS[role.position_type]??role.position_type}
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
