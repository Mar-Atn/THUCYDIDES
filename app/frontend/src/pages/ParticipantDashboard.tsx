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
  { key:'economic', label:'Economic', actions:[
    {id:'set_budget',label:'Set Budget'},{id:'set_tariffs',label:'Set Tariffs'},
    {id:'set_sanctions',label:'Set Sanctions'},{id:'set_opec',label:'Set Cartel Production'},
  ]},
  { key:'intl', label:'International Affairs & Trade', actions:[
    {id:'propose_transaction',label:'Propose Transaction'},
    {id:'propose_agreement',label:'Propose Agreement'},
    {id:'basing_rights',label:'Grant / Revoke Basing Rights'},
  ]},
  { key:'military', label:'Military', actions:[
    {id:'ground_attack',label:'Ground Attack'},{id:'air_strike',label:'Air Strike'},{id:'naval_combat',label:'Naval Combat'},
    {id:'naval_bombardment',label:'Naval Bombardment'},{id:'launch_missile_conventional',label:'Missile Launch'},
    {id:'naval_blockade',label:'Naval Blockade'},{id:'move_units',label:'Move Units (inter-round)'},
    {id:'martial_law',label:'Martial Law'},{id:'nuclear_test',label:'Nuclear Test'},
    {id:'nuclear_launch_initiate',label:'Nuclear Launch'},{id:'nuclear_authorize',label:'Authorize Nuclear'},
    {id:'nuclear_intercept',label:'Intercept Missiles'},
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
            : <TabActions roleActions={roleActions} currentPhase={simState?.current_phase??'pre'} onSelectAction={setActiveAction}
                simId={simId!} countryId={myRole.country_id} roleId={myRole.id}/>
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

function TabActions({roleActions, currentPhase, onSelectAction, simId, countryId, roleId}:{
  roleActions:string[]; currentPhase:string; onSelectAction:(id:string)=>void
  simId:string; countryId:string; roleId:string
}) {
  const avail = new Set(roleActions)
  const [pendingTxns, setPendingTxns] = useState<{id:string;proposer:string;offer:Record<string,unknown>;request:Record<string,unknown>;terms:string;created_at:string}[]>([])
  const [reviewTxn, setReviewTxn] = useState<string|null>(null)
  const [reviewAgr, setReviewAgr] = useState<string|null>(null)

  const [pendingAgreements, setPendingAgreements] = useState<{id:string;agreement_name:string;agreement_type:string;proposer_country_code:string;signatories:string[];terms:string;signatures:Record<string,unknown>}[]>([])

  const loadPendingTxns = useCallback(()=>{
    supabase.from('exchange_transactions')
      .select('id,proposer,counterpart,offer,request,terms,created_at')
      .eq('sim_run_id',simId).eq('counterpart',countryId).eq('status','pending')
      .then(({data})=>setPendingTxns((data??[]) as typeof pendingTxns))
    // Also load agreements awaiting our signature
    supabase.from('agreements')
      .select('id,agreement_name,agreement_type,proposer_country_code,signatories,terms,signatures')
      .eq('sim_run_id',simId).eq('status','proposed').contains('signatories',[countryId])
      .then(({data})=>{
        // Filter to ones we haven't signed yet
        const unsigned = (data??[]).filter((a:Record<string,unknown>)=>{
          const sigs = (a.signatures as Record<string,{confirmed?:boolean}>)||{}
          return !sigs[countryId]?.confirmed
        })
        setPendingAgreements(unsigned as typeof pendingAgreements)
      })
  },[simId,countryId])

  useEffect(()=>{
    loadPendingTxns()
    // Poll every 10s for new proposals (Realtime may not cover all cases)
    const interval = setInterval(loadPendingTxns, 10000)
    return ()=>clearInterval(interval)
  },[loadPendingTxns])

  // If reviewing a transaction, show the review screen
  const txnToReview = reviewTxn ? pendingTxns.find(t=>t.id===reviewTxn) : null
  if (txnToReview) {
    return <TransactionReview txn={txnToReview} simId={simId} countryId={countryId} roleId={roleId}
      onClose={()=>setReviewTxn(null)}
      onDone={()=>{setReviewTxn(null);setPendingTxns(prev=>prev.filter(t=>t.id!==txnToReview.id))}} />
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
            setReviewAgr(null); setPendingAgreements(prev=>prev.filter(a=>a.id!==agrToReview.id))
          }} disabled={signingAgr===agrToReview.id}
            className="bg-success text-white font-body text-body-sm font-medium px-6 py-2.5 rounded-lg hover:bg-success/90 disabled:opacity-50 transition-colors">
            {signingAgr===agrToReview.id?'Signing...':'Sign Agreement'}</button>
          <button onClick={async()=>{
            setSigningAgr(agrToReview.id)
            await handleSignAgreement(agrToReview.id,false)
            setReviewAgr(null); setPendingAgreements(prev=>prev.filter(a=>a.id!==agrToReview.id))
          }} disabled={signingAgr===agrToReview.id}
            className="bg-danger/10 text-danger font-body text-body-sm font-medium px-6 py-2.5 rounded-lg hover:bg-danger/20 transition-colors">
            Decline</button>
          <button onClick={()=>setReviewAgr(null)} className="font-body text-body-sm text-text-secondary hover:text-text-primary px-4 py-2.5">Cancel</button>
        </div>
      </div>
    )
  }

  const [signingAgr, setSigningAgr] = useState<string|null>(null)

  const handleSignAgreement = async (agrId:string, confirm:boolean) => {
    setSigningAgr(agrId)
    try {
      await submitAction(simId,'sign_agreement',roleId,countryId,{
        agreement_id:agrId, confirm, comments:'',
      })
      setPendingAgreements(prev=>prev.filter(a=>a.id!==agrId))
    } catch(e) { alert(e instanceof Error?e.message:'Failed') }
    finally { setSigningAgr(null) }
  }

  const hasExpected = pendingTxns.length > 0 || pendingAgreements.length > 0

  return (
    <div className="space-y-4">
      {/* Actions Expected Now */}
      <div className={`border rounded-lg p-4 ${hasExpected?'bg-warning/10 border-warning/30':'bg-warning/5 border-warning/20'}`}>
        <h3 className="font-heading text-h3 text-warning mb-2">Actions Expected Now{hasExpected?` (${pendingTxns.length})`:''}</h3>
        {!hasExpected
          ? <p className="font-body text-caption text-text-secondary">No urgent actions at this time.</p>
          : <div className="grid grid-cols-2 lg:grid-cols-3 gap-2">
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
          </div>
        }
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
  if (actionType === 'set_budget') return <BudgetForm {...{roleId,countryId,simId,onClose,onSubmitted}} />
  if (actionType === 'set_tariffs') return <TariffSanctionForm type="tariffs" {...{roleId,countryId,simId,onClose,onSubmitted}} />
  if (actionType === 'set_sanctions') return <TariffSanctionForm type="sanctions" {...{roleId,countryId,simId,onClose,onSubmitted}} />
  if (actionType === 'set_opec') return <CartelProductionForm {...{roleId,countryId,simId,onClose,onSubmitted}} />
  if (actionType === 'propose_transaction') return <ProposeTransactionForm {...{roleId,countryId,simId,onClose,onSubmitted}} />
  if (actionType === 'propose_agreement') return <ProposeAgreementForm {...{roleId,countryId,simId,onClose,onSubmitted}} />

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

/* ── Transaction Review (counterpart response) ─────────────────────────── */

function TransactionReview({txn,simId,countryId,roleId,onClose,onDone}:{
  txn:{id:string;proposer:string;offer:Record<string,unknown>;request:Record<string,unknown>;terms:string}
  simId:string;countryId:string;roleId:string;onClose:()=>void;onDone:()=>void
}) {
  const [myCountry,setMyCountry]=useState<Record<string,unknown>|null>(null)
  const [myReserves,setMyReserves]=useState<{unit_type:string;count:number}[]>([])
  const [submitting,setSubmitting]=useState(false)
  const [result,setResult]=useState<string|null>(null)
  const [error,setError]=useState<string|null>(null)
  const [showCounter,setShowCounter]=useState(false)
  const [counterComment,setCounterComment]=useState('')

  useEffect(()=>{
    supabase.from('countries').select('*').eq('sim_run_id',simId).eq('id',countryId).limit(1)
      .then(({data})=>{if(data?.[0]) setMyCountry(data[0])})
    // Count reserves by type
    supabase.from('deployments').select('unit_type').eq('sim_run_id',simId).eq('country_id',countryId).eq('unit_status','reserve')
      .then(({data})=>{
        const counts: Record<string,number> = {}
        ;(data??[]).forEach((d:{unit_type:string})=>{counts[d.unit_type]=(counts[d.unit_type]||0)+1})
        setMyReserves(Object.entries(counts).map(([unit_type,count])=>({unit_type,count})))
      })
  },[simId,countryId])

  const summarize = (a:Record<string,unknown>) => {
    const items: {label:string;ok?:boolean}[] = []
    const coins = Number(a.coins||0)
    if (coins>0) items.push({label:`${coins} coins`})
    const units = a.units as {type:string;count:number}[]|string[]|undefined
    if (units && Array.isArray(units) && units.length>0) {
      if (typeof units[0]==='string') items.push({label:`${units.length} specific units`})
      else (units as {type:string;count:number}[]).forEach(u=>items.push({label:`${u.count} ${u.type.replace('_',' ')}`}))
    }
    const tech = a.technology as {type:string;level:number}|undefined
    if (tech && tech.type) items.push({label:`${tech.type} technology L${tech.level}`})
    if (a.basing_rights) items.push({label:'Basing rights'})
    return items.length>0 ? items : [{label:'Nothing'}]
  }

  // Check if we can fulfill what's requested
  const requested = txn.request
  const issues: string[] = []
  if (myCountry) {
    const reqCoins = Number(requested.coins||0)
    if (reqCoins > 0 && reqCoins > Number(myCountry.treasury||0)) issues.push(`Insufficient treasury: need ${reqCoins}, have ${Number(myCountry.treasury||0).toFixed(0)}`)
    const reqUnits = requested.units as {type:string;count:number}[]|undefined
    if (reqUnits && Array.isArray(reqUnits)) {
      reqUnits.forEach(ru=>{
        if (typeof ru === 'object' && ru.type) {
          const have = myReserves.find(r=>r.unit_type===ru.type)?.count||0
          if (have < ru.count) issues.push(`Insufficient ${ru.type.replace('_',' ')}: need ${ru.count}, have ${have} in reserve`)
        }
      })
    }
    const reqTech = requested.technology as {type:string;level:number}|undefined
    if (reqTech && reqTech.type) {
      const myLevel = reqTech.type==='nuclear' ? Number(myCountry.nuclear_level||0) : Number(myCountry.ai_level||0)
      if (myLevel < reqTech.level) issues.push(`Insufficient ${reqTech.type} technology: need L${reqTech.level}, have L${myLevel}`)
    }
  }
  const canAccept = issues.length === 0

  const handleResponse = async (response:'accept'|'decline') => {
    setSubmitting(true); setError(null)
    try {
      await submitAction(simId,'accept_transaction',roleId,countryId,{transaction_id:txn.id, response})
      setResult(response==='accept'?'Transaction accepted — assets transferred':'Transaction declined')
    } catch(e) { setError(e instanceof Error?e.message:'Failed') }
    finally { setSubmitting(false) }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h2 className="font-heading text-h2 text-text-primary">Transaction Proposal from {txn.proposer}</h2>
          {myCountry&&<span className="font-body text-caption text-text-secondary bg-card border border-border rounded px-3 py-1">Our Treasury: <span className="font-data text-text-primary">{Number(myCountry.treasury??0).toFixed(0)} coins</span></span>}
        </div>
        <button onClick={onClose} className="font-body text-caption text-text-secondary hover:text-text-primary px-3 py-1 rounded border border-border">← Back</button>
      </div>

      {txn.terms&&<div className="bg-card border border-border rounded-lg p-4 italic">
        <span className="font-body text-caption text-text-secondary">Message: </span>
        <span className="font-body text-body-sm text-text-primary">"{txn.terms}"</span>
      </div>}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* What they offer us */}
        <div className="bg-card border-2 border-success/20 rounded-lg p-5">
          <h3 className="font-heading text-body-sm text-success uppercase tracking-wider mb-3">They Offer Us</h3>
          <div className="space-y-2">
            {summarize(txn.offer).map((item,i)=>
              <div key={i} className="font-body text-body-sm text-text-primary bg-success/5 rounded px-3 py-2">{item.label}</div>
            )}
          </div>
        </div>

        {/* What they request from us */}
        <div className="bg-card border-2 border-action/20 rounded-lg p-5">
          <h3 className="font-heading text-body-sm text-action uppercase tracking-wider mb-3">They Request From Us</h3>
          <div className="space-y-2">
            {summarize(txn.request).map((item,i)=>
              <div key={i} className="font-body text-body-sm text-text-primary bg-action/5 rounded px-3 py-2">{item.label}</div>
            )}
          </div>
        </div>
      </div>

      {/* Availability check */}
      {issues.length>0&&<div className="bg-danger/5 border border-danger/20 rounded-lg p-4">
        <h3 className="font-heading text-caption text-danger uppercase tracking-wider mb-2">Cannot Accept — Missing Assets</h3>
        {issues.map((issue,i)=><p key={i} className="font-body text-body-sm text-danger">{issue}</p>)}
      </div>}

      {/* Actions */}
      {!showCounter&&<div className="flex items-center gap-3">
        <button onClick={()=>handleResponse('accept')} disabled={submitting||!canAccept}
          className="bg-success text-white font-body text-body-sm font-medium px-6 py-2.5 rounded-lg hover:bg-success/90 disabled:opacity-50 transition-colors">
          {submitting?'Processing...':'Accept Deal'}</button>
        <button onClick={()=>handleResponse('decline')} disabled={submitting}
          className="bg-danger/10 text-danger font-body text-body-sm font-medium px-6 py-2.5 rounded-lg hover:bg-danger/20 transition-colors">
          Decline</button>
        <button onClick={()=>setShowCounter(true)}
          className="bg-warning/10 text-warning font-body text-body-sm font-medium px-6 py-2.5 rounded-lg hover:bg-warning/20 transition-colors">
          Counteroffer</button>
        <button onClick={onClose} className="font-body text-body-sm text-text-secondary hover:text-text-primary px-4 py-2.5">Cancel</button>
      </div>}

      {/* Counteroffer form */}
      {showCounter&&<div className="bg-card border-2 border-warning/30 rounded-lg p-5 space-y-3">
        <h3 className="font-heading text-body-sm text-warning uppercase tracking-wider">Counteroffer</h3>
        <p className="font-body text-caption text-text-secondary">
          Adjust the terms and send back. The original proposal will be declined and a new proposal sent from you to {txn.proposer}.
        </p>
        <textarea value={counterComment} onChange={e=>setCounterComment(e.target.value)}
          placeholder="Add a message explaining your counter-proposal..."
          rows={2} className="w-full bg-base border border-border rounded px-3 py-2 font-body text-body-sm text-text-primary resize-none"/>
        <div className="flex items-center gap-3">
          <button disabled={submitting} onClick={async ()=>{
            setSubmitting(true); setError(null)
            try {
              // Decline original
              await submitAction(simId,'accept_transaction',roleId,countryId,{transaction_id:txn.id, response:'decline', rationale:'Counteroffer sent'})
              // Create new proposal (swap sides — coins/tech/basing only, units need manual selection)
              const counterOffer: Record<string,unknown> = {}
              const counterRequest: Record<string,unknown> = {}
              // Swap coins
              if (txn.request.coins) counterOffer.coins = txn.request.coins
              if (txn.offer.coins) counterRequest.coins = txn.offer.coins
              // Swap tech
              if (txn.request.technology && Object.keys(txn.request.technology as object).length>0) counterOffer.technology = txn.request.technology
              if (txn.offer.technology && Object.keys(txn.offer.technology as object).length>0) counterRequest.technology = txn.offer.technology
              // Swap basing
              if (txn.request.basing_rights) counterOffer.basing_rights = txn.request.basing_rights
              if (txn.offer.basing_rights) counterRequest.basing_rights = txn.offer.basing_rights
              // Units: request as type+count (not swapped as unit_ids)
              if (txn.offer.units && Array.isArray(txn.offer.units) && (txn.offer.units as unknown[]).length>0) {
                // They offered specific units — we request same type+count back
                const unitReqs = (txn.offer.units as string[]).reduce((acc:{type:string;count:number}[], uid)=>{
                  // Can't determine type from unit_id alone — skip for now
                  return acc
                }, [])
                if (unitReqs.length>0) counterRequest.units = unitReqs
              }

              await submitAction(simId,'propose_transaction',roleId,countryId,{
                proposer_country_code:countryId, counterpart_country_code:txn.proposer,
                scope:'country',
                offer: counterOffer,
                request: counterRequest,
                rationale: counterComment || 'Counteroffer',
                visibility: 'public',
              })
              setResult('Counteroffer sent — original proposal declined')
            } catch(e) { setError(e instanceof Error?e.message:'Failed') }
            finally { setSubmitting(false) }
          }}
            className="bg-warning text-white font-body text-body-sm font-medium px-6 py-2.5 rounded-lg hover:bg-warning/90 disabled:opacity-50 transition-colors">
            {submitting?'Sending...':'Send Counteroffer'}</button>
          <button onClick={()=>setShowCounter(false)} className="font-body text-body-sm text-text-secondary hover:text-text-primary px-4 py-2.5">Cancel</button>
        </div>
      </div>}

      {result&&<div className="bg-success/5 border border-success/20 rounded-lg p-3">
        <p className="font-body text-body-sm text-success">{result}</p>
        <button onClick={onDone} className="font-body text-caption text-action hover:underline mt-1">← Return to Actions</button>
      </div>}
      {error&&<div className="bg-danger/5 border border-danger/20 rounded-lg p-3"><p className="font-body text-body-sm text-danger">{error}</p></div>}
    </div>
  )
}

/* ── Propose Agreement Form ─────────────────────────────────────────────── */

const AGREEMENT_TYPES = [
  {value:'military_alliance', label:'Military Alliance', relation:'alliance'},
  {value:'trade_agreement', label:'Trade Agreement', relation:'economic_partnership'},
  {value:'peace_treaty', label:'Peace Treaty', relation:'neutral'},
  {value:'ceasefire', label:'Ceasefire', relation:'hostile'},
]

function ProposeAgreementForm({roleId,countryId,simId,onClose,onSubmitted}:{
  roleId:string;countryId:string;simId:string;onClose:()=>void;onSubmitted:()=>void
}) {
  const [countries,setCountries]=useState<{id:string;sim_name:string;color_ui:string|null}[]>([])
  const [agrType,setAgrType]=useState('trade_agreement')
  const [agrName,setAgrName]=useState('')
  const [terms,setTerms]=useState('')
  const [signatories,setSignatories]=useState<Set<string>>(new Set())
  const [secret,setSecret]=useState(false)
  const [submitting,setSubmitting]=useState(false)
  const [result,setResult]=useState<string|null>(null)
  const [error,setError]=useState<string|null>(null)
  const [pendingAgr,setPendingAgr]=useState<{id:string;agreement_name:string;signatories:string[];status:string;signatures:Record<string,unknown>}[]>([])

  useEffect(()=>{
    supabase.from('countries').select('id,sim_name,color_ui').eq('sim_run_id',simId).order('sim_name')
      .then(({data})=>setCountries((data??[]).filter((c:{id:string})=>c.id!==countryId) as typeof countries))
    // Load pending/active agreements involving our country
    supabase.from('agreements').select('id,agreement_name,agreement_type,signatories,status,signatures')
      .eq('sim_run_id',simId).contains('signatories',[countryId])
      .then(({data})=>setPendingAgr((data??[]) as typeof pendingAgr))
  },[simId,countryId])

  const toggleSignatory=(id:string)=>{
    setSignatories(prev=>{const n=new Set(prev);if(n.has(id))n.delete(id);else n.add(id);return n})
  }

  const canSubmit = agrName.trim().length>=3 && signatories.size>=1 && agrType

  const handleSubmit = async()=>{
    setSubmitting(true);setError(null)
    try {
      const allSignatories = [countryId, ...Array.from(signatories)]
      await submitAction(simId,'propose_agreement',roleId,countryId,{
        proposer_country_code:countryId, proposer_role_id:roleId,
        agreement_name:agrName.trim(),
        agreement_type:agrType,
        signatories:allSignatories,
        terms:terms.trim(),
        visibility:secret?'secret':'public',
        round_num:1,
      })
      setResult(`Agreement "${agrName}" proposed — awaiting signatures from ${signatories.size} countr${signatories.size>1?'ies':'y'}`)
    } catch(e){setError(e instanceof Error?e.message:'Failed')}
    finally{setSubmitting(false)}
  }

  const typeInfo = AGREEMENT_TYPES.find(t=>t.value===agrType)

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="font-heading text-h2 text-text-primary">Propose Agreement</h2>
        <button onClick={onClose} className="font-body text-caption text-text-secondary hover:text-text-primary px-3 py-1 rounded border border-border">← Back</button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
        {/* LEFT: Agreement form */}
        <div className="lg:col-span-3 space-y-3">
          {/* Type */}
          <div className="bg-card border border-border rounded-lg p-4">
            <h3 className="font-heading text-caption text-text-secondary uppercase tracking-wider mb-2">Agreement Type</h3>
            <div className="flex gap-2">
              {AGREEMENT_TYPES.map(t=>
                <button key={t.value} onClick={()=>setAgrType(t.value)}
                  className={`flex-1 font-body text-caption py-2 px-3 rounded border transition-colors text-center ${
                    agrType===t.value?'bg-action text-white border-action font-medium':'bg-base border-border text-text-secondary hover:border-action/30'
                  }`}>{t.label}</button>
              )}
            </div>
            {typeInfo&&<p className="font-body text-caption text-text-secondary mt-2">
              Sets bilateral relationship to: <strong className="text-text-primary">{typeInfo.relation}</strong>
            </p>}
          </div>

          {/* Name */}
          <div className="bg-card border border-border rounded-lg p-4">
            <h3 className="font-heading text-caption text-text-secondary uppercase tracking-wider mb-2">Agreement Name</h3>
            <input type="text" value={agrName} onChange={e=>setAgrName(e.target.value)}
              placeholder="e.g. Columbia-Cathay Trade Framework 2027"
              className="w-full bg-base border border-border rounded px-3 py-2 font-body text-body-sm text-text-primary"/>
          </div>

          {/* Signatories */}
          <div className="bg-card border border-border rounded-lg p-4">
            <h3 className="font-heading text-caption text-text-secondary uppercase tracking-wider mb-2">Signatories (select countries)</h3>
            <div className="flex flex-wrap gap-2">
              {countries.map(c=>{
                const sel=signatories.has(c.id)
                return <button key={c.id} onClick={()=>toggleSignatory(c.id)}
                  className={`inline-flex items-center gap-1.5 font-body text-caption px-3 py-1.5 rounded border transition-colors ${
                    sel?'bg-action/10 text-action border-action/30 font-medium':'bg-base border-border text-text-secondary hover:border-action/20'
                  }`}>
                  <div className="w-2.5 h-2.5 rounded" style={{backgroundColor:c.color_ui??'#666'}}/>
                  {c.sim_name}
                </button>
              })}
            </div>
          </div>

          {/* Terms */}
          <div className="bg-card border border-border rounded-lg p-4">
            <h3 className="font-heading text-caption text-text-secondary uppercase tracking-wider mb-2">Terms</h3>
            <textarea value={terms} onChange={e=>setTerms(e.target.value)}
              placeholder="Describe the terms of the agreement..."
              rows={4} className="w-full bg-base border border-border rounded px-3 py-2 font-body text-body-sm text-text-primary resize-none"/>
          </div>

          {/* Options + Submit */}
          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" checked={secret} onChange={e=>setSecret(e.target.checked)} className="accent-danger"/>
              <span className="font-body text-caption text-text-secondary">Secret agreement</span>
            </label>
          </div>
          <div className="flex items-center gap-3">
            <button onClick={handleSubmit} disabled={submitting||!canSubmit}
              className="bg-action text-white font-body text-body-sm font-medium px-6 py-2.5 rounded-lg hover:bg-action/90 disabled:opacity-50 transition-colors">
              {submitting?'Sending...':'Propose Agreement'}</button>
            <button onClick={onClose} className="font-body text-body-sm text-text-secondary hover:text-text-primary px-4 py-2.5">Cancel</button>
          </div>
          {result&&<div className="bg-success/5 border border-success/20 rounded-lg p-3">
            <p className="font-body text-body-sm text-success">{result}</p>
            <button onClick={onSubmitted} className="font-body text-caption text-action hover:underline mt-1">← Return to Actions</button>
          </div>}
          {error&&<div className="bg-danger/5 border border-danger/20 rounded-lg p-3"><p className="font-body text-body-sm text-danger">{error}</p></div>}
        </div>

        {/* RIGHT: Existing agreements */}
        <div className="lg:col-span-2 space-y-3">
          <h3 className="font-heading text-body-sm text-text-primary">Our Agreements</h3>
          {pendingAgr.length===0
            ? <p className="font-body text-caption text-text-secondary bg-card border border-border rounded-lg p-4">No agreements yet.</p>
            : <div className="space-y-2">
              {pendingAgr.map(a=>{
                const sigs = a.signatures as Record<string,{confirmed?:boolean}>
                const signedCount = Object.values(sigs).filter(s=>s?.confirmed).length
                const totalNeeded = (a.signatories||[]).length
                return <div key={a.id} className={`bg-card border rounded-lg p-3 ${a.status==='active'?'border-success/30':'border-border'}`}>
                  <div className="flex items-center justify-between">
                    <span className="font-body text-body-sm text-text-primary font-medium">{a.agreement_name}</span>
                    <span className={`font-data text-caption ${a.status==='active'?'text-success':'text-warning'}`}>{a.status}</span>
                  </div>
                  <div className="font-body text-caption text-text-secondary mt-1">
                    {(a.signatories||[]).join(', ')} · {signedCount}/{totalNeeded} signed
                  </div>
                </div>
              })}
            </div>
          }
        </div>
      </div>
    </div>
  )
}

/* ── Propose Transaction Form ───────────────────────────────────────────── */

const UNIT_TYPES_TRADE = ['ground','naval','tactical_air','strategic_missile','air_defense'] as const

function ProposeTransactionForm({roleId,countryId,simId,onClose,onSubmitted}:{
  roleId:string;countryId:string;simId:string;onClose:()=>void;onSubmitted:()=>void
}) {
  const [countries,setCountries]=useState<{id:string;sim_name:string;color_ui:string|null}[]>([])
  const [myReserves,setMyReserves]=useState<{unit_id:string;unit_type:string}[]>([])
  const [myCountry,setMyCountry]=useState<Record<string,unknown>|null>(null)
  const [counterpart,setCounterpart]=useState('')
  const [secret,setSecret]=useState(false)
  const [comment,setComment]=useState('')
  // Offer
  const [offerCoins,setOfferCoins]=useState(0)
  const [offerUnits,setOfferUnits]=useState<string[]>([])  // unit_ids from reserve
  const [offerTechType,setOfferTechType]=useState<'none'|'nuclear'|'ai'>('none')
  const [offerTechLevel,setOfferTechLevel]=useState(0)
  const [offerBasing,setOfferBasing]=useState(false)
  // Request
  const [reqCoins,setReqCoins]=useState(0)
  const [reqUnits,setReqUnits]=useState<Record<string,number>>({})  // type → count
  const [reqTechType,setReqTechType]=useState<'none'|'nuclear'|'ai'>('none')
  const [reqTechLevel,setReqTechLevel]=useState(0)
  const [reqBasing,setReqBasing]=useState(false)

  const [submitting,setSubmitting]=useState(false)
  const [result,setResult]=useState<string|null>(null)
  const [error,setError]=useState<string|null>(null)

  useEffect(()=>{
    supabase.from('countries').select('id,sim_name,color_ui').eq('sim_run_id',simId).order('sim_name')
      .then(({data})=>setCountries((data??[]).filter((c:{id:string})=>c.id!==countryId) as typeof countries))
    supabase.from('deployments').select('unit_id,unit_type').eq('sim_run_id',simId).eq('country_id',countryId).eq('unit_status','reserve')
      .then(({data})=>setMyReserves((data??[]) as typeof myReserves))
    supabase.from('countries').select('*').eq('sim_run_id',simId).eq('id',countryId).limit(1)
      .then(({data})=>{if(data?.[0]) setMyCountry(data[0])})
  },[simId,countryId])

  const [outgoing, setOutgoing] = useState<{id:string;counterpart:string;status:string}[]>([])

  useEffect(()=>{
    supabase.from('exchange_transactions').select('id,counterpart,status')
      .eq('sim_run_id',simId).eq('proposer',countryId).in_('status',['pending','countered'])
      .then(({data})=>setOutgoing((data??[]) as typeof outgoing))
  },[simId,countryId])

  const handleWithdraw = async (txnId:string) => {
    if (!confirm('Withdraw this transaction proposal?')) return
    try {
      await supabase.from('exchange_transactions').update({status:'withdrawn'}).eq('id',txnId)
      setOutgoing(prev=>prev.filter(t=>t.id!==txnId))
    } catch { /* ignore */ }
  }

  const treasury = Number(myCountry?.treasury??0)
  const myNuclear = Number(myCountry?.nuclear_level??0)
  const myAI = Number(myCountry?.ai_level??0)

  // Group reserves by type
  const reserveByType: Record<string,string[]> = {}
  myReserves.forEach(u=>{
    reserveByType[u.unit_type] = reserveByType[u.unit_type]||[]
    reserveByType[u.unit_type].push(u.unit_id)
  })

  const hasOffer = offerCoins>0||offerUnits.length>0||offerTechType!=='none'||offerBasing
  const hasRequest = reqCoins>0||Object.values(reqUnits).some(v=>v>0)||reqTechType!=='none'||reqBasing
  const canSubmit = counterpart && (hasOffer||hasRequest)

  const handleSubmit = async () => {
    setSubmitting(true); setError(null)
    try {
      const offer: Record<string,unknown> = {}
      const request: Record<string,unknown> = {}
      if (offerCoins>0) offer.coins = offerCoins
      if (offerUnits.length>0) offer.units = offerUnits
      if (offerTechType!=='none') offer.technology = {type:offerTechType, level:offerTechLevel}
      if (offerBasing) offer.basing_rights = {grant:true}
      if (reqCoins>0) request.coins = reqCoins
      const unitReqs = Object.entries(reqUnits).filter(([,v])=>v>0).map(([t,c])=>({type:t,count:c}))
      if (unitReqs.length>0) request.units = unitReqs
      if (reqTechType!=='none') request.technology = {type:reqTechType, level:reqTechLevel}
      if (reqBasing) request.basing_rights = {grant:true}

      await submitAction(simId,'propose_transaction',roleId,countryId,{
        proposer_country_code:countryId, counterpart_country_code:counterpart,
        scope:'country', offer, request,
        rationale:comment, visibility:secret?'secret':'public',
      })
      setResult('Transaction proposed — awaiting counterpart response')
    } catch(e) { setError(e instanceof Error?e.message:'Failed') }
    finally { setSubmitting(false) }
  }

  const Sec = ({title,children}:{title:string;children:React.ReactNode}) => (
    <div className="bg-card border border-border rounded-lg p-4 space-y-3">
      <h3 className="font-heading text-caption text-text-secondary uppercase tracking-wider">{title}</h3>
      {children}
    </div>
  )

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="font-heading text-h2 text-text-primary">Propose Transaction</h2>
        <button onClick={onClose} className="font-body text-caption text-text-secondary hover:text-text-primary px-3 py-1 rounded border border-border">← Back</button>
      </div>

      {/* Treasury + outgoing offers */}
      <div className="flex items-center gap-4">
        <div className="bg-card border border-border rounded-lg px-4 py-2">
          <span className="font-body text-caption text-text-secondary">Our Treasury: </span>
          <span className="font-data text-data text-text-primary">{treasury.toFixed(0)} coins</span>
        </div>
        {outgoing.length>0&&<div className="flex items-center gap-2 flex-1">
          <span className="font-body text-caption text-text-secondary">Pending offers:</span>
          {outgoing.map(o=>
            <span key={o.id} className="inline-flex items-center gap-1 bg-card border border-border rounded px-2 py-1">
              <span className="font-body text-caption text-text-primary">→ {o.counterpart}</span>
              <button onClick={()=>handleWithdraw(o.id)} className="text-danger/50 hover:text-danger text-sm leading-none" title="Withdraw">✕</button>
            </span>
          )}
        </div>}
      </div>

      {/* Counterpart + options */}
      <div className="flex items-center gap-4">
        <div className="flex-1">
          <label className="font-body text-caption text-text-secondary block mb-1">Trading with</label>
          <select value={counterpart} onChange={e=>setCounterpart(e.target.value)}
            className="w-full bg-base border border-border rounded px-3 py-2 font-body text-body-sm text-text-primary">
            <option value="">Select country...</option>
            {countries.map(c=><option key={c.id} value={c.id}>{c.sim_name}</option>)}
          </select>
        </div>
        <label className="flex items-center gap-2 cursor-pointer mt-5">
          <input type="checkbox" checked={secret} onChange={e=>setSecret(e.target.checked)} className="accent-danger"/>
          <span className="font-body text-caption text-text-secondary">Secret deal</span>
        </label>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* LEFT: What we offer */}
        <div className="space-y-3">
          <h3 className="font-heading text-body-sm text-success">We Offer</h3>

          <Sec title="Coins">
            <div className="flex items-center gap-2">
              <input type="number" min="0" max={treasury} value={offerCoins} onChange={e=>setOfferCoins(Math.max(0,parseInt(e.target.value)||0))}
                className="w-24 bg-base border border-border rounded px-2 py-1 font-data text-body-sm text-right"/>
              <span className="font-body text-caption text-text-secondary">of {treasury.toFixed(0)} available</span>
            </div>
          </Sec>

          <Sec title="Military Units (from Reserve)">
            {Object.keys(reserveByType).length===0
              ? <p className="font-body text-caption text-text-secondary">No reserve units available</p>
              : Object.entries(reserveByType).map(([type,ids])=>
                <div key={type} className="space-y-1">
                  <div className="font-body text-caption text-text-primary capitalize">{type.replace('_',' ')} ({ids.length} in reserve)</div>
                  <div className="flex flex-wrap gap-1">
                    {ids.map(uid=>{
                      const sel = offerUnits.includes(uid)
                      return <button key={uid} onClick={()=>setOfferUnits(prev=>sel?prev.filter(x=>x!==uid):[...prev,uid])}
                        className={`font-data text-caption px-2 py-0.5 rounded border transition-colors ${sel?'bg-success text-white border-success':'bg-base border-border text-text-secondary hover:border-success/30'}`}>
                        {uid.split('_').pop()}
                      </button>
                    })}
                  </div>
                </div>
              )
            }
          </Sec>

          <Sec title="Technology">
            <div className="space-y-2">
              {myNuclear>0&&<div>
                <div className="font-body text-caption text-text-secondary mb-1">Nuclear (we have L{myNuclear})</div>
                <div className="flex gap-1">
                  <button onClick={()=>{setOfferTechType(offerTechType==='nuclear'&&offerTechLevel===0?'none':'nuclear');setOfferTechLevel(0)}}
                    className={`font-data text-caption px-3 py-1 rounded border transition-colors ${offerTechType!=='nuclear'?'bg-base border-border text-text-secondary':'bg-base border-border text-text-secondary'}`}>None</button>
                  {Array.from({length:myNuclear},(_,i)=>i+1).map(l=>
                    <button key={l} onClick={()=>{setOfferTechType('nuclear');setOfferTechLevel(l)}}
                      className={`font-data text-caption px-3 py-1 rounded border transition-colors ${offerTechType==='nuclear'&&offerTechLevel===l?'bg-success text-white border-success':'bg-base border-border text-text-secondary hover:border-success/30'}`}>
                      L{l}
                    </button>
                  )}
                </div>
              </div>}
              {myAI>0&&<div>
                <div className="font-body text-caption text-text-secondary mb-1">AI (we have L{myAI})</div>
                <div className="flex gap-1">
                  <button onClick={()=>{setOfferTechType(offerTechType==='ai'&&offerTechLevel===0?'none':'ai');setOfferTechLevel(0)}}
                    className={`font-data text-caption px-3 py-1 rounded border transition-colors ${offerTechType!=='ai'?'bg-base border-border text-text-secondary':'bg-base border-border text-text-secondary'}`}>None</button>
                  {Array.from({length:myAI},(_,i)=>i+1).map(l=>
                    <button key={l} onClick={()=>{setOfferTechType('ai');setOfferTechLevel(l)}}
                      className={`font-data text-caption px-3 py-1 rounded border transition-colors ${offerTechType==='ai'&&offerTechLevel===l?'bg-success text-white border-success':'bg-base border-border text-text-secondary hover:border-success/30'}`}>
                      L{l}
                    </button>
                  )}
                </div>
              </div>}
              {myNuclear===0&&myAI===0&&<p className="font-body text-caption text-text-secondary">No technology to offer</p>}
            </div>
          </Sec>

          <Sec title="Basing Rights">
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" checked={offerBasing} onChange={e=>setOfferBasing(e.target.checked)} className="accent-action"/>
              <span className="font-body text-body-sm text-text-primary">Grant access to our territory</span>
            </label>
          </Sec>
        </div>

        {/* RIGHT: What we request */}
        <div className="space-y-3">
          <h3 className="font-heading text-body-sm text-action">We Request</h3>

          <Sec title="Coins">
            <div className="flex items-center gap-2">
              <input type="number" min="0" max="999" value={reqCoins} onChange={e=>setReqCoins(Math.max(0,parseInt(e.target.value)||0))}
                className="w-24 bg-base border border-border rounded px-2 py-1 font-data text-body-sm text-right"/>
              <span className="font-body text-caption text-text-secondary">coins</span>
            </div>
          </Sec>

          <Sec title="Military Units">
            <div className="space-y-2">
              {UNIT_TYPES_TRADE.map(type=>
                <div key={type} className="flex items-center gap-2">
                  <span className="font-body text-caption text-text-primary w-28 capitalize">{type.replace('_',' ')}</span>
                  <input type="number" min="0" max="20" value={reqUnits[type]??0}
                    onChange={e=>setReqUnits(p=>({...p,[type]:Math.max(0,parseInt(e.target.value)||0)}))}
                    className="w-16 bg-base border border-border rounded px-2 py-1 font-data text-caption text-right"/>
                </div>
              )}
            </div>
          </Sec>

          <Sec title="Technology">
            <div className="space-y-2">
              <div>
                <div className="font-body text-caption text-text-secondary mb-1">Nuclear</div>
                <div className="flex gap-1">
                  <button onClick={()=>{if(reqTechType==='nuclear')setReqTechType('none');setReqTechLevel(0)}}
                    className={`font-data text-caption px-3 py-1 rounded border transition-colors ${reqTechType!=='nuclear'?'bg-base border-border text-text-secondary':'bg-base border-border text-text-secondary'}`}>None</button>
                  {[1,2,3].map(l=>
                    <button key={l} onClick={()=>{setReqTechType('nuclear');setReqTechLevel(l)}}
                      className={`font-data text-caption px-3 py-1 rounded border transition-colors ${reqTechType==='nuclear'&&reqTechLevel===l?'bg-action text-white border-action':'bg-base border-border text-text-secondary hover:border-action/30'}`}>
                      L{l}
                    </button>
                  )}
                </div>
              </div>
              <div>
                <div className="font-body text-caption text-text-secondary mb-1">AI</div>
                <div className="flex gap-1">
                  <button onClick={()=>{if(reqTechType==='ai')setReqTechType('none');setReqTechLevel(0)}}
                    className={`font-data text-caption px-3 py-1 rounded border transition-colors ${reqTechType!=='ai'?'bg-base border-border text-text-secondary':'bg-base border-border text-text-secondary'}`}>None</button>
                  {[1,2,3,4].map(l=>
                    <button key={l} onClick={()=>{setReqTechType('ai');setReqTechLevel(l)}}
                      className={`font-data text-caption px-3 py-1 rounded border transition-colors ${reqTechType==='ai'&&reqTechLevel===l?'bg-action text-white border-action':'bg-base border-border text-text-secondary hover:border-action/30'}`}>
                      L{l}
                    </button>
                  )}
                </div>
              </div>
            </div>
          </Sec>

          <Sec title="Basing Rights">
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" checked={reqBasing} onChange={e=>setReqBasing(e.target.checked)} className="accent-action"/>
              <span className="font-body text-body-sm text-text-primary">Request access to their territory</span>
            </label>
          </Sec>
        </div>
      </div>

      {/* Comment + Submit */}
      <div className="bg-card border border-border rounded-lg p-4 space-y-3">
        <textarea value={comment} onChange={e=>setComment(e.target.value)} placeholder="Add a message to the counterpart (optional)..."
          rows={2} className="w-full bg-base border border-border rounded px-3 py-2 font-body text-body-sm text-text-primary resize-none"/>
        <div className="flex items-center gap-3">
          <button onClick={handleSubmit} disabled={submitting||!canSubmit}
            className="bg-action text-white font-body text-body-sm font-medium px-6 py-2.5 rounded-lg hover:bg-action/90 disabled:opacity-50 transition-colors">
            {submitting?'Sending...':'Send Proposal'}</button>
          <button onClick={onClose} className="font-body text-body-sm text-text-secondary hover:text-text-primary px-4 py-2.5">Cancel</button>
          {!canSubmit&&counterpart&&<span className="font-body text-caption text-warning">Add at least one item to offer or request</span>}
        </div>
        {result&&<div className="bg-success/5 border border-success/20 rounded-lg p-3">
          <p className="font-body text-body-sm text-success">{result}</p>
          <button onClick={onSubmitted} className="font-body text-caption text-action hover:underline mt-1">← Return to Actions</button>
        </div>}
        {error&&<div className="bg-danger/5 border border-danger/20 rounded-lg p-3"><p className="font-body text-body-sm text-danger">{error}</p></div>}
      </div>
    </div>
  )
}

/* ── Cartel Production Form ─────────────────────────────────────────────── */

const OIL_LEVELS: {v:string;l:string;pct:number}[] = [
  {v:'min',l:'Minimum',pct:60},{v:'low',l:'Low',pct:80},{v:'normal',l:'Normal',pct:100},
  {v:'high',l:'High',pct:120},{v:'max',l:'Maximum',pct:140},
]

function CartelProductionForm({roleId,countryId,simId,onClose,onSubmitted}:{
  roleId:string;countryId:string;simId:string;onClose:()=>void;onSubmitted:()=>void
}) {
  const [producers, setProducers] = useState<{id:string;sim_name:string;mbpd:number;prod:string;cartel:boolean}[]>([])
  const [myProd, setMyProd] = useState('normal')
  const [oilPrice, setOilPrice] = useState(80)
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState<string|null>(null)
  const [error, setError] = useState<string|null>(null)

  useEffect(()=>{
    supabase.from('countries')
      .select('id,sim_name,oil_producer,opec_member,opec_production,oil_production_mbpd')
      .eq('sim_run_id',simId).eq('oil_producer',true)
      .then(({data})=>{
        const prods = (data??[]).map((c:Record<string,unknown>)=>({
          id: c.id as string, sim_name: c.sim_name as string,
          mbpd: Number(c.oil_production_mbpd??0),
          prod: (c.opec_production as string)||'normal',
          cartel: !!(c.opec_member),
        }))
        setProducers(prods)
        const mine = prods.find(p=>p.id===countryId)
        if (mine) setMyProd(mine.prod==='na'?'normal':mine.prod)
      })
    supabase.from('world_state').select('oil_price')
      .eq('sim_run_id',simId).order('round_num',{ascending:false}).limit(1)
      .then(({data})=>{if(data?.[0]) setOilPrice(Number(data[0].oil_price))})
  },[simId,countryId])

  // Calculate global production as % of normal
  const totalNormal = producers.reduce((s,p)=>s+p.mbpd, 0)
  const totalActual = producers.reduce((s,p)=>{
    const pct = (p.id===countryId ? OIL_LEVELS.find(l=>l.v===myProd)?.pct??100 : OIL_LEVELS.find(l=>l.v===p.prod)?.pct??100)
    return s + p.mbpd * pct / 100
  }, 0)
  const globalPct = totalNormal > 0 ? Math.round(totalActual / totalNormal * 100) : 100

  const handleSubmit = async () => {
    setSubmitting(true); setError(null)
    try {
      await submitAction(simId, 'set_opec', roleId, countryId, { production_level: myProd })
      setResult('Production level submitted — will take effect in Phase B')
    } catch(e) { setError(e instanceof Error?e.message:'Failed') }
    finally { setSubmitting(false) }
  }

  const myData = producers.find(p=>p.id===countryId)

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="font-heading text-h2 text-text-primary">Set Cartel Production</h2>
        <button onClick={onClose} className="font-body text-caption text-text-secondary hover:text-text-primary px-3 py-1 rounded border border-border">← Back</button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* LEFT: Your decision */}
        <div className="space-y-4">
          <div className="bg-card border-2 border-action/20 rounded-lg p-5">
            <h3 className="font-heading text-body-sm text-action uppercase tracking-wider mb-4">Your Production Level</h3>
            {myData && <p className="font-body text-caption text-text-secondary mb-3">
              Your capacity: {myData.mbpd.toFixed(1)} million barrels/day
            </p>}
            <div className="flex gap-2">
              {OIL_LEVELS.map(l=>
                <button key={l.v} onClick={()=>setMyProd(l.v)}
                  className={`flex-1 font-body text-caption py-2 rounded border transition-colors ${
                    myProd===l.v?'bg-action text-white border-action font-medium':'bg-base border-border text-text-secondary hover:border-action/30'
                  }`}>
                  {l.l}
                </button>
              )}
            </div>
            {myData && <div className="mt-3 font-data text-body-sm text-text-primary">
              Output: {(myData.mbpd * (OIL_LEVELS.find(l=>l.v===myProd)?.pct??100) / 100).toFixed(1)} mbpd
            </div>}
          </div>

          <div className="flex items-center gap-3">
            <button onClick={handleSubmit} disabled={submitting}
              className="bg-action text-white font-body text-body-sm font-medium px-6 py-2.5 rounded-lg hover:bg-action/90 disabled:opacity-50 transition-colors">
              {submitting?'Submitting...':'Submit Production Level'}</button>
            <button onClick={onClose} className="font-body text-body-sm text-text-secondary hover:text-text-primary px-4 py-2.5">Cancel</button>
          </div>
          {result&&<div className="bg-success/5 border border-success/20 rounded-lg p-3">
            <p className="font-body text-body-sm text-success">{result}</p>
            <button onClick={onSubmitted} className="font-body text-caption text-action hover:underline mt-1">← Return to Actions</button>
          </div>}
          {error&&<div className="bg-danger/5 border border-danger/20 rounded-lg p-3"><p className="font-body text-body-sm text-danger">{error}</p></div>}
        </div>

        {/* RIGHT: Global context */}
        <div className="space-y-3">
          <div className="bg-card border border-border rounded-lg p-4">
            <h3 className="font-heading text-caption text-text-secondary uppercase tracking-wider mb-2">Oil Market</h3>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <div className="font-body text-caption text-text-secondary">Current Oil Price</div>
                <div className="font-data text-data-lg text-text-primary">${oilPrice.toFixed(0)}</div>
              </div>
              <div>
                <div className="font-body text-caption text-text-secondary">Global Production</div>
                <div className={`font-data text-data-lg ${globalPct>105?'text-success':globalPct<95?'text-danger':'text-text-primary'}`}>{globalPct}%</div>
              </div>
            </div>
          </div>

          <div className="bg-card border border-border rounded-lg p-4">
            <h3 className="font-heading text-caption text-text-secondary uppercase tracking-wider mb-2">Global Producers</h3>
            <div className="space-y-1">
              {producers.sort((a,b)=>b.mbpd-a.mbpd).map(p=>{
                const pct = OIL_LEVELS.find(l=>l.v===(p.id===countryId?myProd:p.prod))?.pct??100
                const actual = (p.mbpd * pct / 100).toFixed(1)
                return <div key={p.id} className={`flex items-center gap-2 py-1 ${p.id===countryId?'font-medium':''}`}>
                  <span className="font-body text-caption text-text-primary w-20">{p.sim_name}</span>
                  <span className="font-data text-caption text-text-secondary w-14">{p.mbpd.toFixed(1)}</span>
                  <span className={`font-data text-caption w-12 ${pct>100?'text-success':pct<100?'text-warning':'text-text-secondary'}`}>{pct}%</span>
                  <span className="font-data text-caption text-text-primary ml-auto">{actual} mbpd</span>
                  {p.cartel&&<span className="font-body text-caption text-accent">C</span>}
                </div>
              })}
              <div className="border-t border-border pt-1 flex justify-between">
                <span className="font-body text-caption text-text-primary font-medium">Total</span>
                <span className="font-data text-caption text-text-primary font-bold">{totalActual.toFixed(1)} mbpd</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

/* ── Tariff / Sanction Form ─────────────────────────────────────────────── */

function TariffSanctionForm({type,roleId,countryId,simId,onClose,onSubmitted}:{
  type:'tariffs'|'sanctions'; roleId:string; countryId:string; simId:string
  onClose:()=>void; onSubmitted:()=>void
}) {
  const label = type === 'tariffs' ? 'Tariffs' : 'Sanctions'
  const table = type === 'tariffs' ? 'tariffs' : 'sanctions'
  const maxLevel = type === 'tariffs' ? 3 : 3
  const levels = type === 'tariffs'
    ? [{v:0,l:'None'},{v:1,l:'Low'},{v:2,l:'Medium'},{v:3,l:'High'}]
    : [{v:-1,l:'Help Avoid'},{v:0,l:'None'},{v:1,l:'Light'},{v:2,l:'Medium'},{v:3,l:'Heavy'}]

  const [countries, setCountries] = useState<{id:string;sim_name:string;color_ui:string|null}[]>([])
  const [existing, setExisting] = useState<{target:string;level:number}[]>([])
  const [received, setReceived] = useState<{imposer:string;level:number}[]>([])
  const [changes, setChanges] = useState<Record<string,number>>({})
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState<string|null>(null)
  const [error, setError] = useState<string|null>(null)

  useEffect(()=>{
    // Load all countries
    supabase.from('countries').select('id,sim_name,color_ui').eq('sim_run_id',simId).order('sim_name')
      .then(({data})=>setCountries((data??[]).filter((c:{id:string})=>c.id!==countryId) as typeof countries))
    // Load existing imposed by us
    supabase.from(table).select('target_country_id,level').eq('sim_run_id',simId).eq('imposer_country_id',countryId)
      .then(({data})=>{
        const items = (data??[]).map((r:{target_country_id:string;level:number})=>({target:r.target_country_id,level:r.level}))
        setExisting(items)
        const ch: Record<string,number> = {}
        items.forEach(i=>{ch[i.target]=i.level})
        setChanges(ch)
      })
    // Load received against us
    supabase.from(table).select('imposer_country_id,level').eq('sim_run_id',simId).eq('target_country_id',countryId)
      .then(({data})=>setReceived((data??[]).map((r:{imposer_country_id:string;level:number})=>({imposer:r.imposer_country_id,level:r.level}))))
  },[simId,countryId,table])

  const setLevel = (target:string, level:number) => setChanges(p=>({...p,[target]:level}))
  const hasChanges = Object.entries(changes).some(([t,l])=>{
    const orig = existing.find(e=>e.target===t)
    return orig ? orig.level !== l : l !== 0
  })

  const handleSubmit = async () => {
    setSubmitting(true); setError(null)
    try {
      // Submit each changed target as a separate action
      for (const [target, level] of Object.entries(changes)) {
        const orig = existing.find(e=>e.target===target)
        if (orig && orig.level === level) continue
        if (!orig && level === 0) continue
        await submitAction(simId, type === 'tariffs' ? 'set_tariffs' : 'set_sanctions', roleId, countryId, {
          target_country: target, level,
        })
      }
      setResult(`${label} updated — will take effect in Phase B`)
    } catch(e) { setError(e instanceof Error?e.message:'Failed') }
    finally { setSubmitting(false) }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="font-heading text-h2 text-text-primary">Set {label}</h2>
        <button onClick={onClose} className="font-body text-caption text-text-secondary hover:text-text-primary px-3 py-1 rounded border border-border">← Back</button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* LEFT: Set our tariffs/sanctions */}
        <div className="space-y-3">
          <h3 className="font-heading text-body-sm text-text-primary">{label} We Impose</h3>
          <div className="bg-card border border-border rounded-lg divide-y divide-border">
            {countries.map(c=>{
              const current = changes[c.id] ?? 0
              const orig = existing.find(e=>e.target===c.id)?.level ?? 0
              const changed = current !== orig
              return <div key={c.id} className={`flex items-center gap-3 px-4 py-2 ${changed?'bg-action/5':''}`}>
                <div className="w-3 h-3 rounded shrink-0" style={{backgroundColor:c.color_ui??'#666'}}/>
                <span className="font-body text-body-sm text-text-primary w-24 shrink-0">{c.sim_name}</span>
                <div className="flex gap-1 ml-auto">
                  {levels.map(l=>
                    <button key={l.v} onClick={()=>setLevel(c.id,l.v)}
                      className={`font-data text-caption px-2 py-0.5 rounded border transition-colors ${
                        current===l.v
                          ? l.v>0?'bg-warning text-white border-warning':l.v<0?'bg-success text-white border-success':'bg-text-secondary/20 text-text-secondary border-text-secondary/30'
                          : 'bg-base border-border text-text-secondary hover:border-action/30'
                      }`}>{l.l}</button>
                  )}
                </div>
              </div>
            })}
          </div>

          <div className="flex items-center gap-3">
            <button onClick={handleSubmit} disabled={submitting||!hasChanges}
              className="bg-action text-white font-body text-body-sm font-medium px-6 py-2.5 rounded-lg hover:bg-action/90 disabled:opacity-50 transition-colors">
              {submitting?'Submitting...':`Submit ${label}`}</button>
            <button onClick={onClose} className="font-body text-body-sm text-text-secondary hover:text-text-primary px-4 py-2.5">Cancel</button>
            {!hasChanges&&<span className="font-body text-caption text-text-secondary">No changes</span>}
          </div>
          {result&&<div className="bg-success/5 border border-success/20 rounded-lg p-3">
            <p className="font-body text-body-sm text-success">{result}</p>
            <button onClick={onSubmitted} className="font-body text-caption text-action hover:underline mt-1">← Return to Actions</button>
          </div>}
          {error&&<div className="bg-danger/5 border border-danger/20 rounded-lg p-3"><p className="font-body text-body-sm text-danger">{error}</p></div>}
        </div>

        {/* RIGHT: What's imposed on us */}
        <div className="space-y-3">
          <h3 className="font-heading text-body-sm text-text-primary">{label} Against Us</h3>
          {received.length===0
            ? <p className="font-body text-body-sm text-text-secondary bg-card border border-border rounded-lg p-4">No {label.toLowerCase()} imposed on us.</p>
            : <div className="bg-card border border-border rounded-lg divide-y divide-border">
                {received.map((r,i)=>{
                  const c = countries.find(x=>x.id===r.imposer)
                  return <div key={i} className="flex items-center gap-3 px-4 py-2">
                    <div className="w-3 h-3 rounded shrink-0" style={{backgroundColor:c?.color_ui??'#666'}}/>
                    <span className="font-body text-body-sm text-text-primary">{c?.sim_name??r.imposer}</span>
                    <span className={`font-data text-body-sm ml-auto ${r.level>=2?'text-danger font-bold':r.level>=1?'text-warning':'text-text-secondary'}`}>
                      Level {r.level}
                    </span>
                  </div>
                })}
              </div>
          }
        </div>
      </div>
    </div>
  )
}

/* ── Budget Form ───────────────────────────────────────────────────────── */

const PROD_LEVELS = [{v:0,l:'None'},{v:1,l:'Standard'},{v:2,l:'x2'},{v:3,l:'x3'}]
const BRANCH_COST: Record<string,number> = {ground:3,naval:6,tactical_air:5,strategic_missile:8,air_defense:4}
const PROD_COST_M: Record<number,number> = {0:0,1:1,2:2,3:4}
const PROD_OUT_M: Record<number,number> = {0:0,1:1,2:2,3:3}
const MAINT_MULT = 3.0

function BudgetForm({roleId,countryId,simId,onClose,onSubmitted}:{
  roleId:string;countryId:string;simId:string;onClose:()=>void;onSubmitted:()=>void
}) {
  const [c,setC]=useState<Record<string,unknown>|null>(null)
  const [socialPct,setSocialPct]=useState(1.0)
  const [prod,setProd]=useState<Record<string,number>>({ground:1,naval:0,tactical_air:1,strategic_missile:0,air_defense:0})
  const [nucCoins,setNucCoins]=useState(0)
  const [aiCoins,setAiCoins]=useState(0)
  const [submitting,setSubmitting]=useState(false)
  const [result,setResult]=useState<string|null>(null)
  const [error,setError]=useState<string|null>(null)

  useEffect(()=>{
    supabase.from('countries').select('*').eq('sim_run_id',simId).eq('id',countryId).limit(1)
      .then(({data})=>{if(data?.[0]) setC(data[0])})
  },[simId,countryId])

  if(!c) return <div className="font-body text-body-sm text-text-secondary p-8">Loading budget data...</div>

  const gdp=Number(c.gdp??0), taxRate=Number(c.tax_rate??0.2)
  const revenue=Math.round(gdp*taxRate*10)/10, treasury=Number(c.treasury??0)
  const inflation=Number(c.inflation??0), stability=Number(c.stability??5)
  const socialBaseline=Number(c.social_baseline??0.2)
  const socialBase=Math.round(socialBaseline*revenue*10)/10
  const totalUnits=Number(c.mil_ground??0)+Number(c.mil_naval??0)+Number(c.mil_tactical_air??0)+Number(c.mil_strategic_missiles??0)+Number(c.mil_air_defense??0)
  const maintRate=Number(c.maintenance_per_unit??0.02)
  const maintenance=Math.round(totalUnits*maintRate*MAINT_MULT*10)/10
  const socialSpending=Math.round(socialBase*socialPct*10)/10

  let totalProdCoins=0
  const prodCosts: Record<string,{coins:number;units:number}>={}
  for (const branch of ['ground','naval','tactical_air','strategic_missile','air_defense']) {
    const capKey=branch==='tactical_air'?'prod_cap_tactical':`prod_cap_${branch}`
    const cap=Number(c[capKey]??0)
    const level=prod[branch]??0
    const coins=Math.round(BRANCH_COST[branch]*cap*PROD_COST_M[level])
    const units=Math.round(cap*PROD_OUT_M[level])
    prodCosts[branch]={coins,units}
    totalProdCoins+=coins
  }
  const techBudget=nucCoins+aiCoins
  const totalSpending=maintenance+socialSpending+totalProdCoins+techBudget
  const balance=revenue-totalSpending
  const deficit=balance<0?-balance:0, surplus=balance>0?balance:0
  const coveredByTreasury=Math.min(deficit,treasury)
  const moneyPrinted=deficit>coveredByTreasury?deficit-coveredByTreasury:0
  const expectedTreasury=treasury+surplus-coveredByTreasury

  const handleSubmit=async()=>{
    setSubmitting(true);setError(null)
    try{
      await submitAction(simId,'set_budget',roleId,countryId,{social_pct:socialPct,production:prod,research:{nuclear_coins:nucCoins,ai_coins:aiCoins}})
      setResult('Budget submitted — will be processed in Phase B')
    }catch(e){setError(e instanceof Error?e.message:'Failed')}
    finally{setSubmitting(false)}
  }

  const R=({l,v,b,d,s}:{l:string;v:string;b?:boolean;d?:boolean;s?:boolean})=>(
    <div className={`flex justify-between py-0.5 ${s?'pl-4':''}`}>
      <span className={`font-body text-caption ${d?'text-danger':'text-text-primary'} ${b?'font-medium':''}`}>{l}</span>
      <span className={`font-data text-caption ${d?'text-danger font-bold':'text-text-primary'} ${b?'font-bold':''}`}>{v}</span>
    </div>
  )

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="font-heading text-h2 text-text-primary">National Budget</h2>
        <button onClick={onClose} className="font-body text-caption text-text-secondary hover:text-text-primary px-3 py-1 rounded border border-border">← Back</button>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
        {/* LEFT (3 cols): Budget Decisions */}
        <div className="lg:col-span-3 space-y-3">
          <p className="font-body text-caption text-text-secondary">Set your country's spending priorities. Changes take effect at Phase B.</p>

          {/* Decision 1: Social Spending */}
          <div className="bg-card border-2 border-action/20 rounded-lg p-4">
            <h3 className="font-heading text-body-sm text-action uppercase tracking-wider mb-3">1. Social Spending</h3>
            <div className="flex items-center gap-3 mb-2">
              <span className="font-body text-caption text-text-secondary w-8">50%</span>
              <input type="range" min="0.5" max="1.5" step="0.1" value={socialPct} onChange={e=>setSocialPct(parseFloat(e.target.value))} className="flex-1 accent-action h-2"/>
              <span className="font-body text-caption text-text-secondary w-10">150%</span>
              <span className="font-data text-data-lg text-text-primary w-16 text-right">{(socialPct*100).toFixed(0)}%</span>
            </div>
            <div className="flex justify-between">
              <R l={`Baseline ${socialBase.toFixed(1)} × ${(socialPct*100).toFixed(0)}%`} v={`${socialSpending.toFixed(1)} coins`}/>
              <span className={`font-body text-caption ${socialPct>1?'text-success':socialPct<1?'text-danger':'text-text-secondary'}`}>
                {socialPct>1?`Stability +${((socialPct-1)*4).toFixed(1)}`:socialPct<1?`Stability ${((socialPct-1)*4).toFixed(1)}`:'Neutral'}
              </span>
            </div>
          </div>

          {/* Fixed: Maintenance (not a decision — informational) */}
          <div className="bg-base border border-border rounded-lg p-3">
            <R l={`Fixed: Military Maintenance (${totalUnits} units)`} v={`${maintenance.toFixed(1)} coins`}/>
          </div>

          {/* Decision 2: Military Production */}
          <div className="bg-card border-2 border-action/20 rounded-lg p-4">
            <h3 className="font-heading text-body-sm text-action uppercase tracking-wider mb-3">2. Military Production</h3>
            <div className="space-y-2">
              {['ground','naval','tactical_air'].map(br=>{
                const capKey=br==='tactical_air'?'prod_cap_tactical':`prod_cap_${br}`
                if(Number(c[capKey]??0)===0) return null
                const pc=prodCosts[br]
                return <div key={br} className="flex items-center gap-3">
                  <span className="font-body text-body-sm text-text-primary w-20 capitalize">{br.replace('_',' ')}</span>
                  <div className="flex gap-1">
                    {PROD_LEVELS.map(l=>
                      <button key={l.v} onClick={()=>setProd(p=>({...p,[br]:l.v}))}
                        className={`font-data text-caption px-3 py-1 rounded border transition-colors ${
                          (prod[br]??0)===l.v?'bg-action text-white border-action':'bg-base border-border text-text-secondary hover:border-action/30'
                        }`}>{l.l}</button>
                    )}
                  </div>
                  <span className="font-data text-caption text-text-secondary ml-auto">{pc.units>0?`${pc.units} units`:''}</span>
                  <span className="font-data text-body-sm text-text-primary w-14 text-right">{pc.coins}c</span>
                </div>
              })}
              <div className="border-t border-border pt-2"><R l="Total Production" v={`${totalProdCoins} coins`} b/></div>
            </div>
          </div>

          {/* Decision 3: Technology R&D */}
          <div className="bg-card border-2 border-action/20 rounded-lg p-4">
            <h3 className="font-heading text-body-sm text-action uppercase tracking-wider mb-3">3. Technology Investment</h3>
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-body text-body-sm text-text-primary">Nuclear</span>
                    <span className="font-data text-caption text-text-secondary">Level {Number(c.nuclear_level??0)}</span>
                  </div>
                  <div className="w-full bg-border rounded-full h-1.5">
                    <div className="bg-warning h-1.5 rounded-full" style={{width:`${Number(c.nuclear_rd_progress??0)*100}%`}}/>
                  </div>
                  <span className="font-data text-caption text-text-secondary">{(Number(c.nuclear_rd_progress??0)*100).toFixed(0)}% to next level</span>
                </div>
                <div className="flex items-center gap-1">
                  <input type="number" min="0" max="99" value={nucCoins} onChange={e=>setNucCoins(Math.max(0,parseInt(e.target.value)||0))}
                    className="w-16 bg-base border border-border rounded px-2 py-1 font-data text-body-sm text-text-primary text-right"/>
                  <span className="font-body text-caption text-text-secondary">coins</span>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-body text-body-sm text-text-primary">AI / Semiconductors</span>
                    <span className="font-data text-caption text-text-secondary">Level {Number(c.ai_level??0)}</span>
                  </div>
                  <div className="w-full bg-border rounded-full h-1.5">
                    <div className="bg-accent h-1.5 rounded-full" style={{width:`${Number(c.ai_rd_progress??0)*100}%`}}/>
                  </div>
                  <span className="font-data text-caption text-text-secondary">{(Number(c.ai_rd_progress??0)*100).toFixed(0)}% to next level</span>
                </div>
                <div className="flex items-center gap-1">
                  <input type="number" min="0" max="99" value={aiCoins} onChange={e=>setAiCoins(Math.max(0,parseInt(e.target.value)||0))}
                    className="w-16 bg-base border border-border rounded px-2 py-1 font-data text-body-sm text-text-primary text-right"/>
                  <span className="font-body text-caption text-text-secondary">coins</span>
                </div>
              </div>
              <div className="border-t border-border pt-2"><R l="Total R&D" v={`${techBudget} coins`} b/></div>
            </div>
          </div>
        </div>

        {/* RIGHT (2 cols): Context + Summary */}
        <div className="lg:col-span-2 space-y-3">
          {/* Economic Context */}
          <div className="bg-card border border-border rounded-lg p-4">
            <h3 className="font-heading text-caption text-text-secondary uppercase tracking-wider mb-2">Economic Context</h3>
            <div className="grid grid-cols-2 gap-3 font-data text-caption">
              <div><div className="text-text-secondary">GDP</div><div className="text-data text-text-primary">{gdp.toFixed(1)}</div></div>
              <div><div className="text-text-secondary">Treasury</div><div className="text-data text-text-primary">{treasury.toFixed(1)} coins</div></div>
              <div><div className="text-text-secondary">Inflation</div><div className="text-data text-text-primary">{inflation.toFixed(1)}%</div></div>
              <div><div className="text-text-secondary">Stability</div><div className="text-data text-text-primary">{stability.toFixed(1)}/10</div></div>
            </div>
          </div>

          {/* Revenue */}
          <div className="bg-card border border-border rounded-lg p-4">
            <h3 className="font-heading text-caption text-text-secondary uppercase tracking-wider mb-2">Expected Revenue</h3>
            <R l={`GDP ${gdp.toFixed(1)} × Tax ${(taxRate*100).toFixed(0)}%`} v={`${revenue.toFixed(1)} coins`} b />
          </div>

          {/* Budget Summary */}
          <div className={`bg-card border-2 rounded-lg p-4 ${deficit>0?'border-danger/30':'border-success/20'}`}>
            <h3 className="font-heading text-caption text-text-secondary uppercase tracking-wider mb-2">Budget Summary</h3>
            <R l="Revenue" v={`${revenue.toFixed(1)}`} b/>
            <div className="border-t border-border/50 my-1"/>
            <R l="Social" v={`${socialSpending.toFixed(1)}`} s/>
            <R l="Maintenance" v={`${maintenance.toFixed(1)}`} s/>
            <R l="Production" v={`${totalProdCoins}`} s/>
            <R l="R&D" v={`${techBudget}`} s/>
            <div className="border-t border-border my-1"/>
            <R l="Total Spending" v={`${totalSpending.toFixed(1)}`} b/>
            <div className="border-t border-border my-1"/>
            {surplus>0&&<R l="Surplus → Treasury" v={`+${surplus.toFixed(1)}`}/>}
            {deficit>0&&<>
              <R l="Deficit" v={`-${deficit.toFixed(1)}`} d/>
              <R l={`From Treasury`} v={`-${coveredByTreasury.toFixed(1)}`} s/>
              {moneyPrinted>0&&<R l="Money printed" v={`${moneyPrinted.toFixed(1)}`} s d/>}
            </>}
            <div className="border-t border-border my-1"/>
            <R l="Expected Treasury" v={`${Math.max(0,expectedTreasury).toFixed(1)} coins`} b/>
            {moneyPrinted>0&&<p className="font-body text-caption text-danger mt-2">Warning: money printing will increase inflation.</p>}
          </div>

          {/* Submit */}
          <div className="flex items-center gap-3">
            <button onClick={handleSubmit} disabled={submitting}
              className="bg-action text-white font-body text-body-sm font-medium px-6 py-2.5 rounded-lg hover:bg-action/90 disabled:opacity-50 transition-colors flex-1">
              {submitting?'Submitting...':'Submit Budget'}</button>
            <button onClick={onClose} className="font-body text-body-sm text-text-secondary hover:text-text-primary px-4 py-2.5">Cancel</button>
          </div>
          {result&&<div className="bg-success/5 border border-success/20 rounded-lg p-3">
            <p className="font-body text-body-sm text-success">{result}</p>
            <button onClick={onSubmitted} className="font-body text-caption text-action hover:underline mt-1">← Return to Actions</button>
          </div>}
          {error&&<div className="bg-danger/5 border border-danger/20 rounded-lg p-3"><p className="font-body text-body-sm text-danger">{error}</p></div>}
        </div>
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
