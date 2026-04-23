/**
 * ActionForms.tsx — All action form components for the Participant Dashboard.
 * Extracted from ParticipantDashboard.tsx for maintainability.
 *
 * Each form is a named export used by ActionForm (the router component).
 */

import { useEffect, useState, useCallback, useRef } from 'react'
import { supabase } from '@/lib/supabase'
import { submitAction, getToken } from '@/lib/queries'
import { useRealtimeTable } from '@/hooks/useRealtimeTable'

const API_BASE = import.meta.env.VITE_API_URL ?? ''
import { useCountryList } from '@/hooks/useCountryList'

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

/* ── Shared constants duplicated from ParticipantDashboard ────────────── */

const POS: Record<string, string> = {
  head_of_state: 'Head of State', military_chief: 'Military Chief',
  economy_officer: 'Economy Officer', diplomat: 'Diplomat',
  security: 'Security', opposition: 'Opposition',
  military: 'Military', economy: 'Economy',
}

const RD: Record<number, string> = {
  0:'Pre-Sim',1:'H2 2026',2:'H1 2027',3:'H2 2027',4:'H1 2028',5:'H2 2028',6:'H1 2029',7:'H2 2029',8:'H1 2030',
}

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

/* ── ActionForm — full-screen form for submitting an action ────────────── */

const ACTION_LABELS: Record<string,string> = Object.fromEntries(
  CATS.flatMap(c=>c.actions.map(a=>[a.id,a.label]))
)

export function ActionForm({actionType,roleId,roleName,countryId,simId,onClose,onSubmitted}:{
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
  if (actionType === 'basing_rights') return <BasingRightsForm {...{roleId,countryId,simId,onClose,onSubmitted}} />
  if (actionType === 'declare_war') return <DeclareWarForm {...{roleId,countryId,simId,onClose,onSubmitted}} />
  if (actionType === 'naval_blockade') return <BlockadeForm {...{roleId,countryId,simId,onClose,onSubmitted}} />
  if (actionType === 'martial_law') return <MartialLawForm {...{roleId,countryId,simId,onClose,onSubmitted}} />
  if (actionType === 'nuclear_test') return <NuclearTestForm {...{roleId,countryId,simId,onClose,onSubmitted}} />
  if (actionType === 'nuclear_launch_initiate') return <NuclearLaunchForm {...{roleId,countryId,simId,onClose,onSubmitted}} />
  if (actionType === 'change_leader') return <ChangeLeaderForm {...{roleId,countryId,simId,onClose,onSubmitted}} />
  if (actionType === 'reassign_types') return <ReassignPowersForm {...{roleId,countryId,simId,onClose,onSubmitted}} />
  if (actionType === 'arrest') return <ArrestForm {...{roleId,countryId,simId,onClose,onSubmitted}} />
  if (actionType === 'assassination') return <AssassinationForm {...{roleId,countryId,simId,onClose,onSubmitted}} />
  if (actionType === 'covert_operation') return <CovertOpsForm {...{roleId,countryId,simId,onClose,onSubmitted}} />
  if (actionType === 'intelligence') return <IntelligenceForm {...{roleId,countryId,simId,onClose,onSubmitted}} />
  if (actionType === 'set_meetings' || actionType === 'invite_to_meet' || actionType === 'call_org_meeting') return <SetMeetingsForm {...{roleId,countryId,simId,onClose,onSubmitted}} />

  // Unified attack form — single entry point for all combat types
  if (actionType === 'attack') return <AttackForm {...{roleId,countryId,simId,onClose,onSubmitted}} />
  if (actionType === 'move_units') return <MoveUnitsForm {...{roleId,countryId,simId,onClose,onSubmitted}} />

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

export function PublicStatementForm({roleId,roleName,countryId,simId,onClose,onSubmitted}:{
  roleId:string; roleName:string; countryId:string; simId:string
  onClose:()=>void; onSubmitted:()=>void
}) {
  const [text, setText] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState<string|null>(null)
  const [error, setError] = useState<string|null>(null)
  const [chairedOrgs, setChairedOrgs] = useState<{id:string;name:string}[]>([])
  const [speakingAs, setSpeakingAs] = useState<string>('personal') // 'personal' or org_id

  // Load organizations where this role is chairman
  useEffect(() => {
    supabase.from('organizations').select('id,sim_name,chair_role_id')
      .eq('sim_run_id', simId).eq('chair_role_id', roleId)
      .then(({ data }) => {
        if (data && data.length > 0) {
          setChairedOrgs(data.map(o => ({ id: o.id, name: o.sim_name || o.id })))
        }
      })
  }, [simId, roleId])

  const handleSubmit = async () => {
    if (!text.trim()) return
    setSubmitting(true)
    setError(null)
    try {
      const params: Record<string, string> = { content: text.trim() }
      if (speakingAs !== 'personal') {
        params.org_id = speakingAs
        params.statement_type = 'org_decision'
        const org = chairedOrgs.find(o => o.id === speakingAs)
        if (org) params.org_name = org.name
      }
      const res = await submitAction(simId, 'public_statement', roleId, countryId, params)
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
        {/* Speaking as selector */}
        <div>
          <label className="font-body text-caption text-text-secondary block mb-2">Speaking as</label>
          <div className="space-y-1.5">
            <label className={`flex items-center gap-2 px-3 py-2 rounded cursor-pointer transition-colors ${
              speakingAs === 'personal' ? 'bg-action/5 border border-action/30' : 'hover:bg-base border border-transparent'
            }`}>
              <input type="radio" name="speaking_as" value="personal" checked={speakingAs === 'personal'}
                onChange={() => setSpeakingAs('personal')} className="accent-action"/>
              <span className="font-body text-body-sm text-text-primary">
                <strong>{roleName}</strong> <span className="text-text-secondary">({countryId})</span>
              </span>
            </label>
            {chairedOrgs.map(org => (
              <label key={org.id} className={`flex items-center gap-2 px-3 py-2 rounded cursor-pointer transition-colors ${
                speakingAs === org.id ? 'bg-warning/5 border border-warning/30' : 'hover:bg-base border border-transparent'
              }`}>
                <input type="radio" name="speaking_as" value={org.id} checked={speakingAs === org.id}
                  onChange={() => setSpeakingAs(org.id)} className="accent-warning"/>
                <span className="font-body text-body-sm text-warning font-medium">
                  Official Decision of {org.name}
                </span>
              </label>
            ))}
          </div>
        </div>

        <div>
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
            {submitting ? 'Publishing...' : speakingAs === 'personal' ? 'Publish Statement' : `Publish Official Decision`}
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

export function TransactionReview({txn,simId,countryId,roleId,onClose,onDone}:{
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
    supabase.from('deployments').select('unit_type').eq('sim_run_id',simId).eq('country_code',countryId).eq('unit_status','reserve')
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

/* ── Basing Rights Form ────────────────────────────────────────────────── */

export function BasingRightsForm({roleId,countryId,simId,onClose,onSubmitted}:{
  roleId:string;countryId:string;simId:string;onClose:()=>void;onSubmitted:()=>void
}) {
  const [countries,setCountries]=useState<{id:string;sim_name:string;color_ui:string|null}[]>([])
  const [weGrant,setWeGrant]=useState<string[]>([])   // countries we grant basing to
  const [theyGrant,setTheyGrant]=useState<string[]>([]) // countries that grant us basing
  const [foreignUnits,setForeignUnits]=useState<Record<string,number>>({}) // country → unit count on our soil
  const [submitting,setSubmitting]=useState(false)
  const [result,setResult]=useState<string|null>(null)
  const [error,setError]=useState<string|null>(null)

  useEffect(()=>{
    supabase.from('countries').select('id,sim_name,color_ui').eq('sim_run_id',simId).order('sim_name')
      .then(({data})=>setCountries((data??[]).filter((c:{id:string})=>c.id!==countryId) as typeof countries))

    // Load current basing rights from relationships
    supabase.from('relationships').select('from_country_code,to_country_code,basing_rights_a_to_b,basing_rights_b_to_a')
      .eq('sim_run_id',simId)
      .or(`from_country_code.eq.${countryId},to_country_code.eq.${countryId}`)
      .then(({data})=>{
        const granted:string[]=[], received:string[]=[]
        ;(data??[]).forEach((r:Record<string,unknown>)=>{
          if(r.from_country_code===countryId && r.basing_rights_a_to_b) granted.push(r.to_country_code as string)
          if(r.to_country_code===countryId && r.basing_rights_b_to_a) granted.push(r.from_country_code as string)
          if(r.from_country_code===countryId && r.basing_rights_b_to_a) received.push(r.to_country_code as string)
          if(r.to_country_code===countryId && r.basing_rights_a_to_b) received.push(r.from_country_code as string)
        })
        setWeGrant([...new Set(granted)])
        setTheyGrant([...new Set(received)])
      })

    // Count foreign units on our territory
    // Get our country's hex positions first, then count foreign units at those hexes
    supabase.from('deployments').select('global_row,global_col')
      .eq('sim_run_id',simId).eq('country_code',countryId).eq('unit_status','active')
      .then(({data:ourUnits})=>{
        const ourHexes = new Set((ourUnits??[]).filter((u:{global_row:number|null})=>u.global_row!=null).map((u:{global_row:number;global_col:number})=>`${u.global_row},${u.global_col}`))
        // Now get all foreign active units and check if they're at our hexes
        supabase.from('deployments').select('country_code,global_row,global_col')
          .eq('sim_run_id',simId).neq('country_code',countryId).eq('unit_status','active')
          .then(({data:foreignData})=>{
            const counts:Record<string,number>={}
            ;(foreignData??[]).forEach((d:{country_code:string;global_row:number|null;global_col:number|null})=>{
              if(d.global_row!=null && d.global_col!=null && ourHexes.has(`${d.global_row},${d.global_col}`)){
                counts[d.country_code]=(counts[d.country_code]||0)+1
              }
            })
            setForeignUnits(counts)
          })
      })
  },[simId,countryId])

  const handleGrant = async (guestCountry:string) => {
    if(!confirm(`Grant basing rights to ${guestCountry}? They will be able to place military units on your territory.`)) return
    setSubmitting(true);setError(null)
    try {
      await submitAction(simId,'basing_rights',roleId,countryId,{
        operation:'grant', guest_country:guestCountry,
      })
      setWeGrant(prev=>[...prev,guestCountry])
      setResult(`Basing rights granted to ${guestCountry}`)
    } catch(e){setError(e instanceof Error?e.message:'Failed')}
    finally{setSubmitting(false)}
  }

  const handleRevoke = async (guestCountry:string) => {
    const unitsPresent = foreignUnits[guestCountry]||0
    if(unitsPresent>0) {
      alert(`Cannot revoke basing rights from ${guestCountry} — they have ${unitsPresent} units on your territory. They must withdraw first.`)
      return
    }
    if(!confirm(`Revoke basing rights from ${guestCountry}?`)) return
    setSubmitting(true);setError(null)
    try {
      await submitAction(simId,'basing_rights',roleId,countryId,{
        operation:'revoke', guest_country:guestCountry,
      })
      setWeGrant(prev=>prev.filter(c=>c!==guestCountry))
      setResult(`Basing rights revoked from ${guestCountry}`)
    } catch(e){setError(e instanceof Error?e.message:'Failed')}
    finally{setSubmitting(false)}
  }

  const notGranted = countries.filter(c=>!weGrant.includes(c.id))

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="font-heading text-h2 text-text-primary">Basing Rights</h2>
        <button onClick={onClose} className="font-body text-caption text-text-secondary hover:text-text-primary px-3 py-1 rounded border border-border">← Back</button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* LEFT: Rights we grant */}
        <div className="space-y-3">
          <h3 className="font-heading text-body-sm text-text-primary">We Grant Access To</h3>

          {weGrant.length===0
            ? <p className="font-body text-caption text-text-secondary bg-card border border-border rounded-lg p-4">No countries have basing rights on our territory.</p>
            : <div className="bg-card border border-border rounded-lg divide-y divide-border">
              {weGrant.map(cc=>{
                const c=countries.find(x=>x.id===cc)
                const units=foreignUnits[cc]||0
                return <div key={cc} className="flex items-center gap-3 px-4 py-2">
                  <div className="w-3 h-3 rounded" style={{backgroundColor:c?.color_ui??'#666'}}/>
                  <span className="font-body text-body-sm text-text-primary flex-1">{c?.sim_name??cc}</span>
                  {units>0&&<span className="font-body text-caption text-warning">{units} units present</span>}
                  <button onClick={()=>handleRevoke(cc)} disabled={submitting||units>0}
                    className={`font-body text-caption px-3 py-1 rounded transition-colors ${
                      units>0?'text-text-secondary/30 cursor-not-allowed':'text-danger hover:bg-danger/10'
                    }`}>Revoke</button>
                </div>
              })}
            </div>
          }

          {/* Grant to new country */}
          {notGranted.length>0&&<div className="bg-card border-2 border-action/20 rounded-lg p-4">
            <h3 className="font-heading text-caption text-action uppercase tracking-wider mb-2">Grant Basing Rights</h3>
            <div className="flex flex-wrap gap-2">
              {notGranted.map(c=>
                <button key={c.id} onClick={()=>handleGrant(c.id)} disabled={submitting}
                  className="inline-flex items-center gap-1.5 font-body text-caption px-3 py-1.5 rounded border border-border text-text-secondary hover:border-action/30 hover:text-action transition-colors">
                  <div className="w-2.5 h-2.5 rounded" style={{backgroundColor:c.color_ui??'#666'}}/>
                  {c.sim_name}
                </button>
              )}
            </div>
          </div>}
        </div>

        {/* RIGHT: Rights we receive */}
        <div className="space-y-3">
          <h3 className="font-heading text-body-sm text-text-primary">We Have Access To</h3>
          {theyGrant.length===0
            ? <p className="font-body text-caption text-text-secondary bg-card border border-border rounded-lg p-4">No countries have granted us basing rights.</p>
            : <div className="bg-card border border-border rounded-lg divide-y divide-border">
              {theyGrant.map(cc=>{
                const c=countries.find(x=>x.id===cc)
                return <div key={cc} className="flex items-center gap-3 px-4 py-2">
                  <div className="w-3 h-3 rounded" style={{backgroundColor:c?.color_ui??'#666'}}/>
                  <span className="font-body text-body-sm text-text-primary">{c?.sim_name??cc}</span>
                  <span className="font-body text-caption text-success ml-auto">Access granted</span>
                </div>
              })}
            </div>
          }
        </div>
      </div>

      {result&&<div className="bg-success/5 border border-success/20 rounded-lg p-3">
        <p className="font-body text-body-sm text-success">{result}</p>
        <button onClick={onSubmitted} className="font-body text-caption text-action hover:underline mt-1">← Return to Actions</button>
      </div>}
      {error&&<div className="bg-danger/5 border border-danger/20 rounded-lg p-3"><p className="font-body text-body-sm text-danger">{error}</p></div>}
    </div>
  )
}

/* ── Blockade Form ────────────────────────────────────────────────────── */

interface ChokepointInfo {
  id: string
  name: string
  hex: number[]
  ground_ok: boolean
  blockade: { imposer: string; level: string; established_round: number } | null
  can_establish: boolean
}

/* ── Martial Law Form ──────────────────────────────────────────────────── */

// Source of truth: engine/config/position_actions.py MARTIAL_LAW_POOLS
const MARTIAL_LAW_POOLS: Record<string,number> = {
  sarmatia: 10, cathay: 10, persia: 8, ruthenia: 6,
}

export function MartialLawForm({roleId,countryId,simId,onClose,onSubmitted}:{
  roleId:string;countryId:string;simId:string;onClose:()=>void;onSubmitted:()=>void
}) {
  const pool = MARTIAL_LAW_POOLS[countryId]
  const eligible = pool !== undefined
  const [alreadyDeclared,setAlreadyDeclared]=useState<boolean|null>(null)
  const [submitting,setSubmitting]=useState(false)
  const [result,setResult]=useState<Record<string,unknown>|null>(null)
  const [error,setError]=useState<string|null>(null)

  useEffect(()=>{
    supabase.from('countries').select('martial_law_declared').eq('sim_run_id',simId).eq('id',countryId).limit(1)
      .then(({data, error: err})=>{
        if (err) { console.warn('martial_law check error:', err); setAlreadyDeclared(false); return }
        setAlreadyDeclared(data?.[0]?.martial_law_declared === true)
      })
  },[simId,countryId])

  const handleDeclare = async () => {
    if(!confirm(`Declare MARTIAL LAW?\n\n• ${pool} conscript ground units added to reserve\n• Stability: -1.0\n• War tiredness: +1.0\n• One-time only — cannot be undone`)) return
    setSubmitting(true); setError(null)
    try {
      const res = await submitAction(simId,'martial_law',roleId,countryId,{})
      setResult(res)
      setAlreadyDeclared(true)
    } catch(e) { setError(e instanceof Error ? e.message : 'Failed') }
    finally { setSubmitting(false) }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="font-heading text-h2 text-text-primary">Martial Law</h2>
        <button onClick={onClose} className="font-body text-caption text-text-secondary hover:text-text-primary px-3 py-1 rounded border border-border">← Back</button>
      </div>

      {!eligible ? (
        <div className="bg-card border border-border rounded-lg p-6">
          <p className="font-body text-body-sm text-text-secondary">Your country is not eligible for martial law declaration.</p>
        </div>
      ) : alreadyDeclared === null ? (
        <div className="bg-card border border-border rounded-lg p-6">
          <p className="font-body text-caption text-text-secondary">Loading...</p>
        </div>
      ) : alreadyDeclared || result ? (
        <div className="bg-card border border-border rounded-lg p-6">
          <p className="font-body text-body-sm text-text-primary font-medium">Martial law declared.</p>
          <p className="font-body text-caption text-text-secondary mt-1">{pool} conscript ground units mobilized to reserve.</p>
        </div>
      ) : (
        <div className="bg-card border border-border rounded-lg p-6 space-y-4">
          <div className="bg-danger/5 border border-danger/20 rounded-lg p-4">
            <p className="font-body text-body-sm text-text-primary">
              Declaring martial law is a <strong className="text-danger">one-time, irreversible</strong> action.
            </p>
          </div>
          <div className="grid grid-cols-3 gap-4 text-center">
            <div className="bg-base rounded-lg p-3">
              <div className="font-data text-data-lg text-action">{pool}</div>
              <div className="font-body text-caption text-text-secondary">Conscript units</div>
            </div>
            <div className="bg-base rounded-lg p-3">
              <div className="font-data text-data-lg text-danger">-1.0</div>
              <div className="font-body text-caption text-text-secondary">Stability</div>
            </div>
            <div className="bg-base rounded-lg p-3">
              <div className="font-data text-data-lg text-warning">+1.0</div>
              <div className="font-body text-caption text-text-secondary">War tiredness</div>
            </div>
          </div>
          <button onClick={handleDeclare} disabled={submitting}
            className="w-full font-body text-caption font-bold uppercase py-3 rounded bg-danger text-white hover:bg-danger/80 transition-colors disabled:opacity-50">
            {submitting ? 'Declaring...' : 'Declare Martial Law'}
          </button>
          {error && <p className="font-body text-caption text-danger">{error}</p>}
        </div>
      )}
    </div>
  )
}

/* ── Nuclear Test Form — dramatic 3-state UX ─────────────────────────────── */

export function NuclearTestForm({roleId,countryId,simId,onClose,onSubmitted}:{
  roleId:string;countryId:string;simId:string;onClose:()=>void;onSubmitted:()=>void
}) {
  const [phase, setPhase] = useState<'idle'|'countdown'|'result'>('idle')
  const [nuclearLevel, setNuclearLevel] = useState<number>(0)
  const [nuclearConfirmed, setNuclearConfirmed] = useState<boolean>(false)
  const [nuclearProgress, setNuclearProgress] = useState<number>(0)
  const [loading, setLoading] = useState(true)
  const [testType, setTestType] = useState<'underground'|'surface'>('underground')
  const [targetHex, setTargetHex] = useState<{row:number,col:number}|null>(null)
  const [countdownNum, setCountdownNum] = useState(5)
  const [result, setResult] = useState<Record<string,unknown>|null>(null)
  const [error, setError] = useState<string|null>(null)
  const mapRef = useRef<HTMLIFrameElement>(null)

  // Listen for hex clicks (surface test site selection)
  useEffect(() => {
    if (testType !== 'surface') return
    const handler = (event: MessageEvent) => {
      const msg = event.data
      if (!msg || msg.type !== 'hex-click') return
      const owner = msg.owner as string
      if (owner === countryId) {
        setTargetHex({row: msg.row as number, col: msg.col as number})
        setError(null)
      } else {
        setError('Must select a hex on your own territory')
      }
    }
    window.addEventListener('message', handler)
    return () => window.removeEventListener('message', handler)
  }, [testType, countryId])

  useEffect(() => {
    if (!simId || !countryId) { setLoading(false); return }
    let cancelled = false
    const timeout = setTimeout(() => { if (!cancelled) setLoading(false) }, 5000)
    setLoading(true)
    supabase.from('countries').select('nuclear_level, nuclear_confirmed, nuclear_rd_progress')
      .eq('sim_run_id', simId).eq('id', countryId).limit(1)
      .then(({data, error: err}) => {
        if (cancelled) return
        if (err) { setError('Failed to load nuclear status'); return }
        const row = data?.[0]
        setNuclearLevel(row?.nuclear_level ?? 0)
        setNuclearConfirmed(row?.nuclear_confirmed === true)
        setNuclearProgress(row?.nuclear_rd_progress ?? 0)
      }).catch(err => console.error('NuclearTestForm load failed:', err))
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true; clearTimeout(timeout) }
  }, [simId, countryId])

  const startTest = async (type: 'underground'|'surface') => {
    setTestType(type)
    setPhase('countdown')
    setCountdownNum(5)

    // Countdown animation
    for (let i = 4; i >= 0; i--) {
      await new Promise(r => setTimeout(r, 1000))
      setCountdownNum(i)
    }

    // Submit to engine
    try {
      const params: Record<string,unknown> = { test_type: type }
      if (type === 'surface' && targetHex) {
        params.target_row = targetHex.row
        params.target_col = targetHex.col
      }
      const res = await submitAction(simId, 'nuclear_test', roleId, countryId, params)
      setResult(res)
      setPhase('result')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Test failed')
      setPhase('idle')
    }
  }

  // Countdown overlay — full-screen dark, device-independent
  if (phase === 'countdown') {
    return (
      <div style={{
        position: 'fixed', inset: 0, zIndex: 50,
        backgroundColor: '#0A0E1A',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        flexDirection: 'column',
      }}>
        <div style={{
          fontFamily: '"JetBrains Mono", "Courier New", monospace',
          color: countdownNum === 0 ? '#FF3C14' : '#00FF41',
          fontSize: '12rem',
          fontWeight: 700,
          lineHeight: 1,
          textShadow: countdownNum === 0
            ? '0 0 60px rgba(255,60,20,0.6), 0 0 120px rgba(255,60,20,0.3)'
            : '0 0 40px rgba(0,255,65,0.4), 0 0 80px rgba(0,255,65,0.2)',
          animation: 'nuclearPulse 1s ease-in-out infinite',
          userSelect: 'none',
        }}>
          {countdownNum === 0 ? 'DETONATION' : countdownNum}
        </div>
        <div style={{
          fontFamily: '"JetBrains Mono", monospace',
          color: '#00FF41',
          fontSize: '1rem',
          opacity: 0.5,
          marginTop: '2rem',
          letterSpacing: '0.3em',
          textTransform: 'uppercase',
        }}>
          {testType} nuclear test in progress
        </div>
        <style>{`
          @keyframes nuclearPulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.03); }
          }
        `}</style>
      </div>
    )
  }

  // Result overlay — full-screen dark, matrix-style reveal
  if (phase === 'result' && result) {
    const testSuccess = result.test_success as boolean
    return (
      <div style={{
        position: 'fixed', inset: 0, zIndex: 50,
        backgroundColor: '#0A0E1A',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        flexDirection: 'column',
        gap: '2rem',
      }}>
        <div style={{
          fontFamily: '"JetBrains Mono", "Courier New", monospace',
          color: testSuccess ? '#00FF41' : '#FF6B35',
          fontSize: '3rem',
          fontWeight: 700,
          letterSpacing: '0.15em',
          textAlign: 'center',
          textShadow: testSuccess
            ? '0 0 30px rgba(0,255,65,0.5)'
            : '0 0 30px rgba(255,107,53,0.5)',
          animation: 'nuclearReveal 1s ease-out forwards',
          maxWidth: '90vw',
        }}>
          {testSuccess
            ? `TEST SUCCESSFUL — LEVEL ${result.nuclear_level} CONFIRMED`
            : 'TEST FAILED — LEVEL NOT CONFIRMED'
          }
        </div>

        {/* Effects summary */}
        <div style={{
          fontFamily: '"JetBrains Mono", monospace',
          color: 'rgba(255,255,255,0.6)',
          fontSize: '0.875rem',
          textAlign: 'center',
          maxWidth: '600px',
          lineHeight: 1.8,
        }}>
          <div>{(result.test_type as string || '').toUpperCase()} TEST</div>
        </div>

        <button
          onClick={() => { setPhase('idle'); onSubmitted() }}
          style={{
            fontFamily: '"JetBrains Mono", monospace',
            color: '#00FF41',
            backgroundColor: 'transparent',
            border: '1px solid rgba(0,255,65,0.3)',
            padding: '0.75rem 2rem',
            fontSize: '0.875rem',
            cursor: 'pointer',
            letterSpacing: '0.1em',
            textTransform: 'uppercase',
            marginTop: '1rem',
          }}
        >
          Return to Actions
        </button>

        <style>{`
          @keyframes nuclearReveal {
            0% { opacity: 0; transform: translateY(20px); }
            100% { opacity: 1; transform: translateY(0); }
          }
        `}</style>
      </div>
    )
  }

  // Idle state — nuclear status + test options
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="font-heading text-h2 text-text-primary">Nuclear Test</h2>
        <button onClick={onClose} className="font-body text-caption text-text-secondary hover:text-text-primary px-3 py-1 rounded border border-border">← Back</button>
      </div>

      {loading ? (
        <div className="bg-card border border-border rounded-lg p-6">
          <p className="font-body text-caption text-text-secondary">Loading nuclear status...</p>
        </div>
      ) : nuclearLevel < 1 ? (
        <div className="bg-card border border-border rounded-lg p-6">
          <p className="font-body text-body-sm text-text-secondary">Your country does not have nuclear capability (level 0). Invest in nuclear R&D first.</p>
        </div>
      ) : (
        <div style={{backgroundColor:'#0A0E1A', borderRadius:'0.5rem', padding:'1.5rem'}}>
          {/* Nuclear Status Panel */}
          <div style={{
            display:'grid', gridTemplateColumns:'1fr 1fr 1fr', gap:'1rem', marginBottom:'1.5rem',
            padding:'1rem', borderRadius:'0.375rem', border:'1px solid rgba(255,255,255,0.1)',
          }}>
            <div style={{textAlign:'center'}}>
              <div style={{fontFamily:'JetBrains Mono, monospace', fontSize:'0.7rem', color:'#9CA3AF', textTransform:'uppercase', letterSpacing:'0.1em'}}>Technology Level</div>
              <div style={{fontFamily:'JetBrains Mono, monospace', fontSize:'2rem', color:'#F59E0B'}}>{nuclearLevel}</div>
            </div>
            <div style={{textAlign:'center'}}>
              <div style={{fontFamily:'JetBrains Mono, monospace', fontSize:'0.7rem', color:'#9CA3AF', textTransform:'uppercase', letterSpacing:'0.1em'}}>Status</div>
              <div style={{fontFamily:'JetBrains Mono, monospace', fontSize:'1rem', marginTop:'0.5rem', color: nuclearConfirmed ? '#00FF41' : '#F59E0B'}}>
                {nuclearConfirmed ? 'CONFIRMED' : 'NOT CONFIRMED'}
              </div>
            </div>
            <div style={{textAlign:'center'}}>
              <div style={{fontFamily:'JetBrains Mono, monospace', fontSize:'0.7rem', color:'#9CA3AF', textTransform:'uppercase', letterSpacing:'0.1em'}}>Progress to Next</div>
              <div style={{fontFamily:'JetBrains Mono, monospace', fontSize:'1rem', marginTop:'0.5rem', color:'#60A5FA'}}>
                {(nuclearProgress * 100).toFixed(0)}%
              </div>
            </div>
          </div>

          {/* Test options — always available */}
          <div style={{marginBottom:'0.5rem', fontFamily:'JetBrains Mono, monospace', fontSize:'0.75rem', color:'#9CA3AF'}}>
            {nuclearConfirmed
              ? 'Level confirmed. A test can still be conducted as a political signal.'
              : 'A successful test is required to confirm current technology level.'}
          </div>
          {/* Effects info */}
          <div style={{
            backgroundColor:'rgba(255,60,20,0.05)', border:'1px solid rgba(255,60,20,0.2)',
            borderRadius:'0.5rem', padding:'1rem', marginBottom:'1.5rem',
            fontFamily:'DM Sans, sans-serif', fontSize:'0.85rem', color:'rgba(255,255,255,0.7)',
          }}>
          </div>

          {/* Surface hex selector — map view */}
          {testType === 'surface' && (
            <div style={{marginBottom:'1rem'}}>
              <div style={{fontFamily:'JetBrains Mono, monospace', fontSize:'0.75rem', color:'rgba(255,255,255,0.5)', marginBottom:'0.5rem'}}>
                Select test site on own territory
              </div>
              {targetHex && (
                <div style={{fontFamily:'JetBrains Mono, monospace', fontSize:'0.85rem', color:'#F59E0B', marginBottom:'0.5rem'}}>
                  Selected: ({targetHex.row}, {targetHex.col})
                </div>
              )}
              <div style={{position:'relative', height:'60vh', minHeight:'400px', borderRadius:'0.5rem', overflow:'hidden', border:'1px solid rgba(255,255,255,0.15)'}}>
                <iframe
                  ref={mapRef}
                  src={`/map/deployments.html?display=clean&mode=attack&country=${countryId}&sim_run_id=${simId}`}
                  style={{position:'absolute', inset:0, width:'100%', height:'100%', border:'none'}}
                  title="Select test site"
                />
              </div>
            </div>
          )}

          {/* Action buttons */}
          <div style={{display:'flex', gap:'1rem'}}>
            <button
              onClick={() => { if(!confirm('Conduct UNDERGROUND nuclear test? This action cannot be undone.')) return; setTestType('underground'); startTest('underground') }}
              style={{
                flex:1, padding:'1rem', borderRadius:'0.5rem', cursor:'pointer',
                backgroundColor:'rgba(245,158,11,0.15)', border:'1px solid rgba(245,158,11,0.4)',
                color:'#F59E0B', fontFamily:'JetBrains Mono, monospace',
                fontSize:'0.85rem', fontWeight:600, textTransform:'uppercase',
                letterSpacing:'0.1em',
              }}
            >
              Underground Test
            </button>
            <button
              onClick={() => {
                if (testType !== 'surface') { setTestType('surface'); return }
                if (!targetHex || !targetHex.row || !targetHex.col) {
                  setError('Select a target hex for surface test')
                  return
                }
                if(!confirm('Conduct SURFACE nuclear test? This will be visible to ALL countries.')) return
                startTest('surface')
              }}
              style={{
                flex:1, padding:'1rem', borderRadius:'0.5rem', cursor:'pointer',
                backgroundColor:'rgba(255,60,20,0.15)', border:'1px solid rgba(255,60,20,0.4)',
                color:'#FF3C14', fontFamily:'JetBrains Mono, monospace',
                fontSize:'0.85rem', fontWeight:600, textTransform:'uppercase',
                letterSpacing:'0.1em',
              }}
            >
              {testType === 'surface' ? 'Confirm Surface Test' : 'Surface Test'}
            </button>
          </div>

          {error && (
            <p style={{fontFamily:'DM Sans, sans-serif', fontSize:'0.8rem', color:'#FF3C14', marginTop:'0.75rem'}}>{error}</p>
          )}
        </div>
      )}
    </div>
  )
}

/* ── Nuclear Launch Form — 4-phase multi-player action ─────────────────── */

interface MissilePair { missileId: string; targetRow: number; targetCol: number }

export function NuclearLaunchForm({roleId,countryId,simId,onClose,onSubmitted}:{
  roleId:string;countryId:string;simId:string;onClose:()=>void;onSubmitted:()=>void
}) {
  const [phase, setPhase] = useState<'select'|'authorizing'|'flight'|'resolved'>('select')
  const [nuclearLevel, setNuclearLevel] = useState(0)
  const [nuclearConfirmed, setNuclearConfirmed] = useState(false)
  const [missiles, setMissiles] = useState<{unit_id:string;unit_type:string;global_row?:number;global_col?:number}[]>([])
  const [pairs, setPairs] = useState<MissilePair[]>([])
  const [selectedMissile, setSelectedMissile] = useState<string|null>(null)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string|null>(null)
  const [nuclearAction, setNuclearAction] = useState<Record<string,unknown>|null>(null)
  const [countdown, setCountdown] = useState<number|null>(null)
  const [result, setResult] = useState<Record<string,unknown>|null>(null)
  const mapRef = useRef<HTMLIFrameElement>(null)
  const pollRef = useRef<ReturnType<typeof setInterval>|null>(null)

  // Load nuclear status + deployed missiles
  useEffect(() => {
    if (!simId || !countryId) { setLoading(false); return }
    let cancelled = false
    const timeout = setTimeout(() => { if (!cancelled) setLoading(false) }, 5000)
    setLoading(true)
    ;(async () => {
      const { data: cs } = await supabase.from('countries')
        .select('nuclear_level, nuclear_confirmed')
        .eq('sim_run_id', simId).eq('id', countryId).limit(1)
      if (cancelled) return
      const row = cs?.[0]
      setNuclearLevel(row?.nuclear_level ?? 0)
      setNuclearConfirmed(row?.nuclear_confirmed === true)

      // Load deployed strategic_missile units
      const { data: deps } = await supabase.from('deployments')
        .select('unit_id, unit_type, unit_status, global_row, global_col')
        .eq('sim_run_id', simId).eq('country_code', countryId)
        .eq('unit_type', 'strategic_missile').eq('unit_status', 'active')
      if (cancelled) return
      setMissiles((deps ?? []) as typeof missiles)
    })().catch(err => console.error('NuclearLaunchForm load failed:', err))
    .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true; clearTimeout(timeout) }
  }, [simId, countryId])

  // Listen for hex clicks (target assignment)
  useEffect(() => {
    if (phase !== 'select' || !selectedMissile) return
    const handler = (event: MessageEvent) => {
      const msg = event.data
      if (!msg || msg.type !== 'hex-click') return
      const owner = msg.owner as string
      if (owner === countryId) {
        setError('Cannot target your own territory')
        return
      }
      setPairs(prev => [...prev, { missileId: selectedMissile, targetRow: msg.row, targetCol: msg.col }])
      setSelectedMissile(null)
      setError(null)
    }
    window.addEventListener('message', handler)
    return () => window.removeEventListener('message', handler)
  }, [phase, selectedMissile, countryId])

  // Poll nuclear action status during authorizing/flight phases
  useEffect(() => {
    if (phase !== 'authorizing' && phase !== 'flight') return
    const poll = async () => {
      try {
        const token = await getToken()
        const resp = await fetch(`${API_BASE}/api/sim/${simId}/nuclear/active`, {
          headers: token ? { 'Authorization': `Bearer ${token}` } : {},
        })
        if (!resp.ok) return
        const json = await resp.json()
        const action = json.data
        if (!action) {
          // No active action — check if resolved
          if (nuclearAction) {
            const { data: resolved } = await supabase.from('nuclear_actions')
              .select('status, resolution').eq('id', (nuclearAction as Record<string,unknown>).id)
              .limit(1)
            if (resolved?.[0]?.status === 'resolved') {
              setResult(resolved[0].resolution as Record<string,unknown>)
              setPhase('resolved')
            } else if (resolved?.[0]?.status === 'cancelled') {
              setError('Launch cancelled — authorization rejected')
              setPhase('select')
            }
          }
          return
        }
        setNuclearAction(action)

        // Update countdown timer
        if (action.timer_started_at) {
          const started = new Date(action.timer_started_at as string).getTime()
          const duration = (action.timer_duration_sec as number) || (action.nuclear_auth_timer_sec as number) || 600
          const remaining = duration - (Date.now() - started) / 1000
          setCountdown(Math.max(0, remaining))
        }

        // Phase transitions
        if (action.status === 'awaiting_interception' && phase === 'authorizing') {
          setPhase('flight')
        }
        if (action.status === 'resolved') {
          setResult(action.resolution as Record<string,unknown>)
          setPhase('resolved')
        }
        if (action.status === 'cancelled') {
          setError('Launch cancelled — authorization rejected')
          setPhase('select')
        }
      } catch { /* ignore polling errors */ }
    }
    poll()
    pollRef.current = setInterval(poll, 2000)
    return () => { if (pollRef.current) clearInterval(pollRef.current) }
  }, [phase, simId, nuclearAction])

  const maxMissiles = nuclearLevel >= 3 ? missiles.length : 1
  const usedMissileIds = new Set(pairs.map(p => p.missileId))
  const availableMissiles = missiles.filter(m => !usedMissileIds.has(m.unit_id))

  const handleInitiate = async () => {
    if (pairs.length === 0) return
    setSubmitting(true); setError(null)
    try {
      const missilePayload = pairs.map(p => ({
        missile_unit_code: p.missileId,
        target_global_row: p.targetRow,
        target_global_col: p.targetCol,
      }))
      const res = await submitAction(simId, 'nuclear_launch_initiate', roleId, countryId, {
        warhead: 'nuclear',
        missiles: missilePayload,
      })
      if (res.status === 'rejected') {
        setError((res.errors as string[])?.join(', ') || 'Launch rejected')
        setSubmitting(false)
        return
      }
      setNuclearAction(res)
      setPhase('authorizing')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed')
    } finally { setSubmitting(false) }
  }

  const removePair = (idx: number) => setPairs(prev => prev.filter((_, i) => i !== idx))

  const fmtCountdown = (s: number) => {
    const m = Math.floor(s / 60)
    const ss = Math.floor(s % 60)
    return `${String(m).padStart(2,'0')}:${String(ss).padStart(2,'0')}`
  }

  // Pre-check: can we launch?
  if (loading) return <div style={{backgroundColor:'#0A0E1A',padding:'2rem',borderRadius:'0.5rem'}}>
    <p style={{fontFamily:'JetBrains Mono, monospace',color:'#9CA3AF',fontSize:'0.8rem'}}>Loading nuclear status...</p>
  </div>

  if (!nuclearConfirmed) return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="font-heading text-h2 text-text-primary">Nuclear Launch</h2>
        <button onClick={onClose} className="font-body text-caption text-text-secondary hover:text-text-primary px-3 py-1 rounded border border-border">← Back</button>
      </div>
      <div style={{backgroundColor:'#0A0E1A',borderRadius:'0.5rem',padding:'1.5rem'}}>
        <p style={{fontFamily:'JetBrains Mono, monospace',color:'#FF6B35',fontSize:'0.9rem'}}>
          Nuclear capability not confirmed. Conduct a successful nuclear test first.
        </p>
      </div>
    </div>
  )

  if (missiles.length === 0) return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="font-heading text-h2 text-text-primary">Nuclear Launch</h2>
        <button onClick={onClose} className="font-body text-caption text-text-secondary hover:text-text-primary px-3 py-1 rounded border border-border">← Back</button>
      </div>
      <div style={{backgroundColor:'#0A0E1A',borderRadius:'0.5rem',padding:'1.5rem'}}>
        <p style={{fontFamily:'JetBrains Mono, monospace',color:'#FF6B35',fontSize:'0.9rem'}}>
          No deployed strategic missiles available. Deploy missiles to launch.
        </p>
      </div>
    </div>
  )

  // RESOLVED phase — full-screen dark result
  if (phase === 'resolved' && result) {
    const hits = (result.hits as number) ?? 0
    const intercepted = (result.missiles_intercepted as number) ?? 0
    const launched = (result.missiles_launched as number) ?? 0
    return (
      <div style={{
        position:'fixed',inset:0,zIndex:50,backgroundColor:'#0A0E1A',
        display:'flex',alignItems:'center',justifyContent:'center',flexDirection:'column',gap:'1.5rem',
      }}>
        <div style={{
          fontFamily:'"JetBrains Mono","Courier New",monospace',
          color: hits > 0 ? '#FF3C14' : '#00FF41',
          fontSize:'2.5rem',fontWeight:700,letterSpacing:'0.1em',textAlign:'center',
          textShadow: hits > 0
            ? '0 0 40px rgba(255,60,20,0.5)'
            : '0 0 40px rgba(0,255,65,0.5)',
          animation:'nuclearReveal 1s ease-out forwards',maxWidth:'90vw',
        }}>
          {hits > 0 ? `NUCLEAR STRIKE — ${hits} IMPACT${hits>1?'S':''}` : 'ALL MISSILES NEUTRALIZED'}
        </div>
        <div style={{
          fontFamily:'"JetBrains Mono",monospace',color:'rgba(255,255,255,0.6)',
          fontSize:'0.875rem',textAlign:'center',lineHeight:1.8,maxWidth:'600px',
        }}>
          <div>Launched: {launched} | Intercepted: {intercepted} | Hits: {hits}</div>
          {(result.damage_log as {military_destroyed:number;nuclear_site_destroyed:boolean}[])?.map((d,i) => (
            <div key={i}>
              Target ({(d as Record<string,unknown>).target_hex as string}): {d.military_destroyed} units destroyed
              {d.nuclear_site_destroyed && ' | NUCLEAR SITE DESTROYED'}
            </div>
          ))}
          {(result.salvo_effects as Record<string,unknown>)?.leader_killed && (
            <div style={{color:'#FF3C14',marginTop:'0.5rem'}}>TARGET LEADER KILLED IN STRIKE</div>
          )}
        </div>
        <button onClick={() => { setPhase('select'); onSubmitted() }} style={{
          fontFamily:'"JetBrains Mono",monospace',color:'#00FF41',backgroundColor:'transparent',
          border:'1px solid rgba(0,255,65,0.3)',padding:'0.75rem 2rem',fontSize:'0.875rem',
          cursor:'pointer',letterSpacing:'0.1em',textTransform:'uppercase',marginTop:'1rem',
        }}>Return to Actions</button>
        <style>{`@keyframes nuclearReveal { 0% { opacity:0; transform:translateY(20px); } 100% { opacity:1; transform:translateY(0); } }`}</style>
      </div>
    )
  }

  // SELECT / AUTHORIZING / FLIGHT — sidebar + map layout
  return (
    <div className="flex gap-3" style={{height:'calc(100vh - 180px)'}}>
      {/* LEFT SIDEBAR — controls (25%) */}
      <div className="w-1/4 min-w-[240px] flex flex-col gap-2 overflow-y-auto pr-1">
        <div className="flex items-center justify-between">
          <h2 className="font-heading text-h3 text-text-primary" style={{color:'#FF3C14'}}>Nuclear Launch</h2>
          <button onClick={onClose} className="font-body text-caption text-text-secondary hover:text-text-primary px-2 py-0.5 rounded border border-border">← Back</button>
        </div>

        <div style={{backgroundColor:'#0A0E1A',borderRadius:'0.5rem',padding:'1rem',flex:1,display:'flex',flexDirection:'column',gap:'0.75rem'}}>
          {/* Nuclear Status */}
          <div style={{display:'flex',gap:'1rem',padding:'0.5rem',borderRadius:'0.25rem',border:'1px solid rgba(255,255,255,0.1)'}}>
            <div style={{textAlign:'center',flex:1}}>
              <div style={{fontFamily:'JetBrains Mono, monospace',fontSize:'0.6rem',color:'#9CA3AF',textTransform:'uppercase',letterSpacing:'0.1em'}}>Level</div>
              <div style={{fontFamily:'JetBrains Mono, monospace',fontSize:'1.5rem',color:'#F59E0B'}}>{nuclearLevel}</div>
            </div>
            <div style={{textAlign:'center',flex:1}}>
              <div style={{fontFamily:'JetBrains Mono, monospace',fontSize:'0.6rem',color:'#9CA3AF',textTransform:'uppercase',letterSpacing:'0.1em'}}>Missiles</div>
              <div style={{fontFamily:'JetBrains Mono, monospace',fontSize:'1.5rem',color:'#FF3C14'}}>{missiles.length}</div>
            </div>
            <div style={{textAlign:'center',flex:1}}>
              <div style={{fontFamily:'JetBrains Mono, monospace',fontSize:'0.6rem',color:'#9CA3AF',textTransform:'uppercase',letterSpacing:'0.1em'}}>Max</div>
              <div style={{fontFamily:'JetBrains Mono, monospace',fontSize:'1.5rem',color:'#FF3C14'}}>{maxMissiles}</div>
            </div>
          </div>

          {/* Phase: SELECT */}
          {phase === 'select' && (<>
            <div style={{fontFamily:'JetBrains Mono, monospace',fontSize:'0.7rem',color:'#9CA3AF',textTransform:'uppercase',letterSpacing:'0.1em'}}>
              Select Missile{maxMissiles > 1 ? 's' : ''} + Assign Target{maxMissiles > 1 ? 's' : ''}
            </div>

            {/* Available missiles — icons only */}
            <div style={{display:'flex',flexWrap:'wrap',gap:'0.5rem',alignItems:'center'}}>
              {availableMissiles.map(m => (
                <button key={m.unit_id} onClick={() => setSelectedMissile(m.unit_id === selectedMissile ? null : m.unit_id)}
                  title={m.unit_id}
                  style={{
                    display:'inline-flex',alignItems:'center',justifyContent:'center',
                    width:'2.5rem',height:'2.5rem',borderRadius:'0.25rem',cursor:'pointer',
                    backgroundColor: m.unit_id === selectedMissile ? 'rgba(255,60,20,0.2)' : 'transparent',
                    border: m.unit_id === selectedMissile ? '2px solid #FF3C14' : '2px solid rgba(255,255,255,0.15)',
                    color: m.unit_id === selectedMissile ? '#FF3C14' : '#9CA3AF',
                  }}>
                  <UnitIcon type="strategic_missile" size={22}/>
                </button>
              ))}
              {availableMissiles.length === 0 && pairs.length > 0 && (
                <span style={{fontFamily:'JetBrains Mono, monospace',fontSize:'0.7rem',color:'#9CA3AF'}}>All missiles assigned</span>
              )}
            </div>

            {selectedMissile && (
              <div style={{fontFamily:'JetBrains Mono, monospace',fontSize:'0.75rem',color:'#FF3C14',
                padding:'0.5rem',borderRadius:'0.25rem',border:'1px solid rgba(255,60,20,0.3)',backgroundColor:'rgba(255,60,20,0.05)',
                display:'flex',alignItems:'center',gap:'0.5rem'}}>
                <UnitIcon type="strategic_missile" size={18}/> Click target hex on map
              </div>
            )}

            {/* Queued missile → target pairs */}
            {pairs.length > 0 && (
              <div style={{display:'flex',flexDirection:'column',gap:'0.25rem'}}>
                <div style={{fontFamily:'JetBrains Mono, monospace',fontSize:'0.65rem',color:'#9CA3AF',textTransform:'uppercase'}}>Launch Queue ({pairs.length})</div>
                {pairs.map((p, i) => (
                  <div key={i} style={{
                    display:'flex',alignItems:'center',justifyContent:'space-between',
                    padding:'0.35rem 0.5rem',borderRadius:'0.25rem',border:'1px solid rgba(255,60,20,0.2)',
                    backgroundColor:'rgba(255,60,20,0.05)',
                  }}>
                    <span style={{display:'flex',alignItems:'center',gap:'0.4rem',color:'#FF3C14'}}>
                      <UnitIcon type="strategic_missile" size={16}/> {'\u2192'} ({p.targetRow},{p.targetCol}) — {hexCountryName(p.targetRow, p.targetCol)} ✓
                    </span>
                    <button onClick={() => removePair(i)} style={{
                      color:'#9CA3AF',cursor:'pointer',border:'none',background:'none',fontSize:'0.8rem',
                    }}>✕</button>
                  </div>
                ))}
              </div>
            )}

            {/* Assigned missiles (red, locked) */}
            {pairs.length > 0 && (
              <div style={{display:'flex',flexWrap:'wrap',gap:'0.5rem',alignItems:'center',marginTop:'0.25rem'}}>
                {pairs.map((p, i) => (
                  <div key={i} title={`Target: (${p.targetRow},${p.targetCol})`}
                    style={{display:'inline-flex',alignItems:'center',justifyContent:'center',
                      width:'2.5rem',height:'2.5rem',borderRadius:'0.25rem',
                      backgroundColor:'rgba(255,60,20,0.2)',border:'2px solid #FF3C14',color:'#FF3C14'}}>
                    <UnitIcon type="strategic_missile" size={22}/>
                  </div>
                ))}
              </div>
            )}

            {/* LAUNCH button — dramatic red */}
            {pairs.length > 0 && (
              <button onClick={() => {
                if(!confirm(`CONFIRM NUCLEAR LAUNCH?\n\n${pairs.length} missile${pairs.length>1?'s':''} will be launched.\nThis action CANNOT be undone.\n\nProceed?`)) return
                handleInitiate()
              }} disabled={submitting}
                style={{
                  width:'100%',padding:'1rem',borderRadius:'0.5rem',cursor:'pointer',
                  backgroundColor:'#991B1B',border:'none',
                  color:'white',fontFamily:'JetBrains Mono, monospace',
                  fontSize:'1rem',fontWeight:700,textTransform:'uppercase',
                  letterSpacing:'0.2em',opacity:submitting?0.5:1,
                  boxShadow:'0 0 20px rgba(153,27,27,0.5)',
                }}>
                {submitting ? 'INITIATING...' : 'CONFIRM LAUNCH'}
              </button>
            )}
          </>)}

          {/* Phase: AUTHORIZING */}
          {phase === 'authorizing' && nuclearAction && (<>
            <div style={{fontFamily:'JetBrains Mono, monospace',fontSize:'0.8rem',color:'#F59E0B',textTransform:'uppercase',letterSpacing:'0.1em'}}>
              Awaiting Authorization
            </div>
            {countdown !== null && (
              <div style={{fontFamily:'JetBrains Mono, monospace',fontSize:'2rem',color:'#F59E0B',textAlign:'center'}}>
                {fmtCountdown(countdown)}
              </div>
            )}
            <div style={{display:'flex',flexDirection:'column',gap:'0.5rem'}}>
              {nuclearAction.authorizer_1_role && (
                <div style={{
                  display:'flex',alignItems:'center',justifyContent:'space-between',
                  padding:'0.5rem',borderRadius:'0.25rem',border:'1px solid rgba(255,255,255,0.1)',
                }}>
                  <span style={{fontFamily:'JetBrains Mono, monospace',fontSize:'0.75rem',color:'#D1D5DB'}}>
                    {nuclearAction.authorizer_1_role as string}
                  </span>
                  <span style={{fontFamily:'JetBrains Mono, monospace',fontSize:'0.85rem',
                    color: nuclearAction.authorizer_1_response === 'confirm' ? '#00FF41'
                      : nuclearAction.authorizer_1_response === 'reject' ? '#FF3C14' : '#F59E0B'
                  }}>
                    {nuclearAction.authorizer_1_response === 'confirm' ? '\u2713'
                      : nuclearAction.authorizer_1_response === 'reject' ? '\u2717' : '\u23F3'}
                  </span>
                </div>
              )}
              {nuclearAction.authorizer_2_role && (
                <div style={{
                  display:'flex',alignItems:'center',justifyContent:'space-between',
                  padding:'0.5rem',borderRadius:'0.25rem',border:'1px solid rgba(255,255,255,0.1)',
                }}>
                  <span style={{fontFamily:'JetBrains Mono, monospace',fontSize:'0.75rem',color:'#D1D5DB'}}>
                    {nuclearAction.authorizer_2_role as string}
                  </span>
                  <span style={{fontFamily:'JetBrains Mono, monospace',fontSize:'0.85rem',
                    color: nuclearAction.authorizer_2_response === 'confirm' ? '#00FF41'
                      : nuclearAction.authorizer_2_response === 'reject' ? '#FF3C14' : '#F59E0B'
                  }}>
                    {nuclearAction.authorizer_2_response === 'confirm' ? '\u2713'
                      : nuclearAction.authorizer_2_response === 'reject' ? '\u2717' : '\u23F3'}
                  </span>
                </div>
              )}
            </div>
          </>)}

          {/* Phase: FLIGHT */}
          {phase === 'flight' && (<>
            <div style={{
              fontFamily:'JetBrains Mono, monospace',fontSize:'1rem',color:'#FF3C14',
              textTransform:'uppercase',letterSpacing:'0.15em',textAlign:'center',
              animation:'nuclearPulse 1.5s ease-in-out infinite',
            }}>
              MISSILES IN FLIGHT
            </div>
            {countdown !== null && (
              <div style={{fontFamily:'JetBrains Mono, monospace',fontSize:'2.5rem',color:'#FF3C14',textAlign:'center',
                textShadow:'0 0 30px rgba(255,60,20,0.4)'}}>
                {fmtCountdown(countdown)}
              </div>
            )}
            <div style={{fontFamily:'JetBrains Mono, monospace',fontSize:'0.7rem',color:'#9CA3AF',textAlign:'center'}}>
              Awaiting interception decisions from T3+ nuclear powers
            </div>
            <style>{`@keyframes nuclearPulse { 0%,100%{transform:scale(1)} 50%{transform:scale(1.03)} }`}</style>
          </>)}

          {error && (
            <div style={{fontFamily:'DM Sans, sans-serif',fontSize:'0.8rem',color:'#FF3C14',
              padding:'0.5rem',borderRadius:'0.25rem',border:'1px solid rgba(255,60,20,0.3)'}}>
              {error}
            </div>
          )}
        </div>
      </div>

      {/* RIGHT: Map (75%) */}
      <div className="flex-1 relative rounded-lg overflow-hidden border border-border">
        <iframe ref={mapRef}
          src={`/map/deployments.html?display=clean&mode=attack&country=${countryId}&sim_run_id=${simId}`}
          className="absolute inset-0 w-full h-full border-0"
          title="Nuclear Target Map" />
      </div>
    </div>
  )
}

export function BlockadeForm({roleId,countryId,simId,onClose,onSubmitted}:{
  roleId:string;countryId:string;simId:string;onClose:()=>void;onSubmitted:()=>void
}) {
  const [chokepoints,setChokepoints]=useState<ChokepointInfo[]>([])
  const [loading,setLoading]=useState(true)
  const [submitting,setSubmitting]=useState(false)
  const [result,setResult]=useState<string|null>(null)
  const [error,setError]=useState<string|null>(null)
  const [selectedLevel,setSelectedLevel]=useState<Record<string,string>>({})

  const loadData = async (signal?: {cancelled:boolean}) => {
    setLoading(true)
    try {
      const token = await getToken()
      const resp = await fetch(`${API_BASE}/api/sim/${simId}/blockades?country=${countryId}`, {
        headers: { 'Authorization': `Bearer ${token}` },
      })
      if (!resp.ok) throw new Error('Failed to load blockade data')
      const json = await resp.json()
      if (signal?.cancelled) return
      setChokepoints(json.data?.chokepoints ?? [])
    } catch (e) {
      if (signal?.cancelled) return
      setError(e instanceof Error ? e.message : 'Failed to load')
    } finally {
      if (!signal?.cancelled) setLoading(false)
    }
  }

  useEffect(() => {
    if (!simId) { setLoading(false); return }
    const signal = {cancelled: false}
    const timeout = setTimeout(() => { if (!signal.cancelled) setLoading(false) }, 5000)
    loadData(signal)
    return () => { signal.cancelled = true; clearTimeout(timeout) }
  }, [simId])

  const handleEstablish = async (zoneId: string) => {
    const level = selectedLevel[zoneId] || 'full'
    setSubmitting(true); setError(null)
    try {
      const res = await submitAction(simId, 'naval_blockade', roleId, countryId, {
        operation: 'establish', zone_id: zoneId, level,
      })
      setResult(res.narrative as string ?? 'Blockade established')
      await loadData()
    } catch (e) { setError(e instanceof Error ? e.message : 'Failed') }
    finally { setSubmitting(false) }
  }

  const handleLift = async (zoneId: string) => {
    if (!confirm('Lift this blockade? Maritime traffic will resume.')) return
    setSubmitting(true); setError(null)
    try {
      const res = await submitAction(simId, 'naval_blockade', roleId, countryId, {
        operation: 'lift', zone_id: zoneId,
      })
      setResult(res.narrative as string ?? 'Blockade lifted')
      await loadData()
    } catch (e) { setError(e instanceof Error ? e.message : 'Failed') }
    finally { setSubmitting(false) }
  }

  const handleReduce = async (zoneId: string) => {
    if (!confirm('Reduce this blockade to partial? Some traffic will be allowed through.')) return
    setSubmitting(true); setError(null)
    try {
      const res = await submitAction(simId, 'naval_blockade', roleId, countryId, {
        operation: 'reduce', zone_id: zoneId,
      })
      setResult(res.narrative as string ?? 'Blockade reduced to partial')
      await loadData()
    } catch (e) { setError(e instanceof Error ? e.message : 'Failed') }
    finally { setSubmitting(false) }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="font-heading text-h2 text-text-primary">Blockade</h2>
        <button onClick={onClose} className="font-body text-caption text-text-secondary hover:text-text-primary px-3 py-1 rounded border border-border">← Back</button>
      </div>

      {loading ? (
        <p className="font-body text-body-sm text-text-secondary">Loading chokepoint data...</p>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {chokepoints.map(cp => (
            <div key={cp.id} className="bg-card border border-border rounded-lg p-4 space-y-3">
              <div>
                <h3 className="font-heading text-body-sm text-text-primary">{cp.name}</h3>
                <p className="font-mono text-caption text-text-secondary">Hex ({cp.hex[0]}, {cp.hex[1]}){cp.ground_ok ? ' — ground support OK' : ''}</p>
              </div>

              {/* Status */}
              {cp.blockade ? (
                <div className={`rounded p-2 ${cp.blockade.imposer === countryId ? 'bg-action/10 border border-action/30' : 'bg-danger/10 border border-danger/30'}`}>
                  <p className="font-body text-caption">
                    <span className={cp.blockade.imposer === countryId ? 'text-action' : 'text-danger'}>
                      {cp.blockade.level.toUpperCase()} BLOCKADE
                    </span>
                    {' '}by {cp.blockade.imposer === countryId ? 'YOU' : cp.blockade.imposer}
                  </p>
                  <p className="font-body text-caption text-text-secondary">Since round {cp.blockade.established_round}</p>
                </div>
              ) : (
                <div className="rounded p-2 bg-background border border-border">
                  <p className="font-body text-caption text-text-secondary">No active blockade</p>
                </div>
              )}

              {/* Actions */}
              {cp.blockade && cp.blockade.imposer === countryId ? (
                <div className="flex gap-2">
                  {cp.blockade.level === 'full' && (
                    <button onClick={() => handleReduce(cp.id)} disabled={submitting}
                      className="font-body text-caption px-3 py-1.5 rounded border border-warning/30 text-warning hover:bg-warning/10 transition-colors">
                      Reduce to Partial
                    </button>
                  )}
                  <button onClick={() => handleLift(cp.id)} disabled={submitting}
                    className="font-body text-caption px-3 py-1.5 rounded border border-danger/30 text-danger hover:bg-danger/10 transition-colors">
                    Lift Blockade
                  </button>
                </div>
              ) : cp.blockade ? (
                <p className="font-body text-caption text-text-secondary">Use Attack to break enemy blockade.</p>
              ) : cp.can_establish ? (
                <div className="space-y-2">
                  <div className="flex gap-3">
                    <label className="flex items-center gap-1.5 cursor-pointer">
                      <input type="radio" name={`level-${cp.id}`} value="full"
                        checked={(selectedLevel[cp.id] || 'full') === 'full'}
                        onChange={() => setSelectedLevel(prev => ({...prev, [cp.id]: 'full'}))}
                        className="accent-action" />
                      <span className="font-body text-caption text-text-primary">Full</span>
                    </label>
                    <label className="flex items-center gap-1.5 cursor-pointer">
                      <input type="radio" name={`level-${cp.id}`} value="partial"
                        checked={selectedLevel[cp.id] === 'partial'}
                        onChange={() => setSelectedLevel(prev => ({...prev, [cp.id]: 'partial'}))}
                        className="accent-action" />
                      <span className="font-body text-caption text-text-primary">Partial</span>
                    </label>
                  </div>
                  <button onClick={() => handleEstablish(cp.id)} disabled={submitting}
                    className="w-full font-body text-caption px-3 py-1.5 rounded bg-action/20 border border-action/30 text-action hover:bg-action/30 transition-colors">
                    Establish Blockade
                  </button>
                </div>
              ) : (
                <p className="font-body text-caption text-text-secondary">No qualifying units at this chokepoint.</p>
              )}
            </div>
          ))}
        </div>
      )}

      {result && <div className="bg-success/5 border border-success/20 rounded-lg p-3">
        <p className="font-body text-body-sm text-success">{result}</p>
        <button onClick={onSubmitted} className="font-body text-caption text-action hover:underline mt-1">← Return to Actions</button>
      </div>}
      {error && <div className="bg-danger/5 border border-danger/20 rounded-lg p-3"><p className="font-body text-body-sm text-danger">{error}</p></div>}
    </div>
  )
}

/* ── Declare War Form ──────────────────────────────────────────────────── */

export function DeclareWarForm({roleId,countryId,simId,onClose,onSubmitted}:{
  roleId:string;countryId:string;simId:string;onClose:()=>void;onSubmitted:()=>void
}) {
  const [countries,setCountries]=useState<{id:string;sim_name:string;color_ui:string|null}[]>([])
  const [relationships,setRelationships]=useState<Record<string,string>>({})
  const [submitting,setSubmitting]=useState(false)
  const [result,setResult]=useState<string|null>(null)
  const [error,setError]=useState<string|null>(null)

  const relColor=(r:string)=>({alliance:'text-success',economic_partnership:'text-action',neutral:'text-text-secondary',hostile:'text-warning',at_war:'text-danger'}[r]??'text-text-secondary')
  const relLabel=(r:string)=>({alliance:'Allied',economic_partnership:'Partnership',neutral:'Neutral',hostile:'Hostile',at_war:'AT WAR'}[r]??r)

  useEffect(()=>{
    supabase.from('countries').select('id,sim_name,color_ui').eq('sim_run_id',simId).order('sim_name')
      .then(({data})=>setCountries((data??[]).filter((c:{id:string})=>c.id!==countryId) as typeof countries))

    supabase.from('relationships').select('to_country_code,relationship')
      .eq('sim_run_id',simId).eq('from_country_code',countryId)
      .then(({data})=>{
        const map:Record<string,string>={}
        ;(data??[]).forEach((r:{to_country_code:string;relationship:string})=>{map[r.to_country_code]=r.relationship})
        setRelationships(map)
      })
  },[simId,countryId])

  const handleDeclare = async (target:string) => {
    const name = countries.find(c=>c.id===target)?.sim_name ?? target
    if(!confirm(`Are you sure you want to declare WAR on ${name}?\n\nThis will immediately set your relationship to AT WAR.`)) return
    setSubmitting(true);setError(null)
    try {
      const res = await submitAction(simId,'declare_war',roleId,countryId,{target_country:target})
      setResult(res.narrative as string ?? `War declared on ${name}`)
      setRelationships(prev=>({...prev,[target]:'at_war'}))
    } catch(e){setError(e instanceof Error?e.message:'Failed')}
    finally{setSubmitting(false)}
  }

  const eligibleTargets = countries.filter(c=>relationships[c.id]!=='at_war')
  const alreadyAtWar = countries.filter(c=>relationships[c.id]==='at_war')

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="font-heading text-h2 text-text-primary">Declare War</h2>
        <button onClick={onClose} className="font-body text-caption text-text-secondary hover:text-text-primary px-3 py-1 rounded border border-border">← Back</button>
      </div>

      <div className="bg-danger/5 border border-danger/20 rounded-lg p-4">
        <p className="font-body text-body-sm text-text-primary">
          Declaring war is <strong className="text-danger">immediate and unilateral</strong>. Both countries' relationship status will be set to <strong className="text-danger">AT WAR</strong>.
        </p>
      </div>

      {/* Countries we can declare war on */}
      {eligibleTargets.length>0 ? (
        <div className="bg-card border border-border rounded-lg divide-y divide-border">
          {eligibleTargets.map(c=>{
            const rel=relationships[c.id]??'neutral'
            return <div key={c.id} className="flex items-center gap-3 px-4 py-3">
              <div className="w-3 h-3 rounded" style={{backgroundColor:c.color_ui??'#666'}}/>
              <span className="font-body text-body-sm text-text-primary flex-1">{c.sim_name}</span>
              <span className={`font-body text-caption ${relColor(rel)}`}>{relLabel(rel)}</span>
              <button onClick={()=>handleDeclare(c.id)} disabled={submitting}
                className="font-body text-caption px-3 py-1.5 rounded bg-danger/10 text-danger hover:bg-danger/20 transition-colors disabled:opacity-50">
                Declare War
              </button>
            </div>
          })}
        </div>
      ) : (
        <div className="bg-card border border-border rounded-lg p-6 text-center">
          <p className="font-body text-body-sm text-text-secondary">Already at war with all countries.</p>
        </div>
      )}

      {/* Already at war */}
      {alreadyAtWar.length>0&&<div className="space-y-2">
        <h3 className="font-heading text-caption text-text-secondary uppercase tracking-wider">Currently At War</h3>
        <div className="bg-card border border-danger/20 rounded-lg divide-y divide-border">
          {alreadyAtWar.map(c=>
            <div key={c.id} className="flex items-center gap-3 px-4 py-2">
              <div className="w-3 h-3 rounded" style={{backgroundColor:c.color_ui??'#666'}}/>
              <span className="font-body text-body-sm text-text-primary flex-1">{c.sim_name}</span>
              <span className="font-body text-caption text-danger font-medium">AT WAR</span>
            </div>
          )}
        </div>
      </div>}

      {result&&<div className="bg-danger/5 border border-danger/20 rounded-lg p-3">
        <p className="font-body text-body-sm text-danger font-medium">{result}</p>
        <button onClick={onSubmitted} className="font-body text-caption text-action hover:underline mt-1">← Return to Actions</button>
      </div>}
      {error&&<div className="bg-danger/5 border border-danger/20 rounded-lg p-3"><p className="font-body text-body-sm text-danger">{error}</p></div>}
    </div>
  )
}

/* ── Unified Attack Form ───────────────────────────────────────────────── */

type AttackStep = 'select_source' | 'select_units' | 'select_target' | 'confirm' | 'result'

interface AttackTarget {
  row: number; col: number; attack_type: string
  enemies: { unit_id: string; country_code: string; unit_type: string }[]
}

const ATTACK_TYPE_LABELS: Record<string,string> = {
  ground_attack: 'Ground Attack', ground_move: 'Advance',
  air_strike: 'Air Strike',
  naval_combat: 'Naval Combat', naval_bombardment: 'Naval Bombardment',
  launch_missile_conventional: 'Missile Launch',
}

const UNIT_TYPE_LABELS: Record<string,string> = {
  ground: 'Ground', tactical_air: 'Tactical Air', naval: 'Naval',
  strategic_missile: 'Strategic Missile', air_defense: 'Air Defense',
}

/** Inline SVG paths for unit type icons (same as map-core.js symbols) */
const UNIT_ICON_PATHS: Record<string,string> = {
  ground: 'M10 8 L18 8 L22 10 L22 11 L10 11 ZM2 13 L5 11 L20 11 L21 13 L21 15 L3 15 ZM2 15 L22 15 C22 18 20 19 18 19 L6 19 C4 19 2 18 2 15 Z',
  tactical_air: 'M12 6 L13 9 L22 12 L22 14 L13 12 L13 16 L15 18 L15 19 L12 18 L9 19 L9 18 L11 16 L11 12 L2 14 L2 12 L11 9 Z',
  naval: 'M2 16 L4 12 L8 12 L8 10 L10 10 L10 8 L12 8 L12 6 L13 6 L13 8 L14 8 L14 10 L16 10 L16 12 L22 12 L22 14 L21 16 Z',
  strategic_missile: 'M12 1 L14.5 6 L14 6 L14 18 L16 18 L16 22 L8 22 L8 18 L10 18 L10 6 L9.5 6 Z',
  air_defense: 'M4 10 C4 5 8 2 12 2 C16 2 20 5 20 10 L18 10 C18 6 15.5 3.5 12 3.5 C8.5 3.5 6 6 6 10 Z M11 9 L13 9 L13 20 L11 20 Z M7 20 L17 20 L17 22 L7 22 Z',
}

export function ArrestedBanner({simId, roleId, round}:{simId:string; roleId:string; round:number}) {
  const [info, setInfo] = useState<{by:string;reason:string}|null>(null)
  useEffect(() => {
    supabase.from('roles').select('status_detail')
      .eq('sim_run_id', simId).eq('id', roleId).limit(1)
      .then(({ data }) => {
        const detail = data?.[0]?.status_detail as Record<string, unknown> | null
        if (detail) {
          setInfo({
            by: (detail.arrested_by_name as string) || (detail.arrested_by as string) || 'Unknown',
            reason: (detail.justification as string) || '',
          })
        }
      })
  }, [simId, roleId])

  return (
    <div className="bg-danger/10 border-b-2 border-danger/40 px-6 py-4">
      <div className="max-w-7xl mx-auto space-y-1">
        <p className="font-heading text-h3 text-danger">You Are Arrested</p>
        <p className="font-body text-body-sm text-text-primary">
          Detained until the end of <strong>{RD[round] || `Round ${round}`}</strong>. All actions are suspended.
        </p>
        {info && (
          <>
            <p className="font-body text-caption text-text-secondary">
              By order of: <strong className="text-text-primary">{info.by}</strong>
            </p>
            {info.reason && (
              <p className="font-body text-caption text-text-secondary">
                Charges: <em className="text-text-primary">{info.reason}</em>
              </p>
            )}
          </>
        )}
      </div>
    </div>
  )
}

export function UnitIcon({type, size=28, className=''}:{type:string;size?:number;className?:string}) {
  const path = UNIT_ICON_PATHS[type] || UNIT_ICON_PATHS.ground
  return (
    <svg viewBox="0 0 24 24" width={size} height={size} className={className} style={{display:'inline-block',verticalAlign:'middle'}}>
      <path d={path} fill="currentColor"/>
    </svg>
  )
}

/** Polls pending_action row for result after moderator confirms. */
export function PendingResultPoller({simId, pendingActionId, countryId, actionType, onResolved}:{
  simId:string; pendingActionId?:string; countryId:string; actionType:string
  onResolved:(result:Record<string,unknown>)=>void
}) {
  const [waiting, setWaiting] = useState(true)
  // Stable ref to avoid useEffect restart on every render
  const onResolvedRef = useRef(onResolved)
  onResolvedRef.current = onResolved

  useEffect(()=>{
    console.log('[PendingResultPoller] started, pendingActionId:', pendingActionId, 'countryId:', countryId)
    // Poll via authenticated fetch (uses cached token, bypasses RLS issues)
    const checkResult = async (): Promise<boolean> => {
      try {
        const token = await getToken()
        const id = pendingActionId
        if (!id) return false
        const url = `/api/sim/${simId}/pending/${id}/status`
        const resp = await fetch(url, {headers: token ? {'Authorization': `Bearer ${token}`} : {}})
        if (!resp.ok) return false
        const body = await resp.json()
        const pa = body.data
        if (pa?.status === 'approved' && pa?.result) {
          console.log('[PendingResultPoller] RESOLVED:', pa.status)
          setWaiting(false)
          onResolvedRef.current({...(pa.result as Record<string,unknown>), pending: false})
          return true
        } else if (pa?.status === 'rejected') {
          console.log('[PendingResultPoller] REJECTED')
          setWaiting(false)
          onResolvedRef.current({pending: false, rejected: true, narrative: 'Attack rejected by moderator'})
          return true
        }
      } catch (e) { console.warn('[PendingResultPoller] error:', e) }
      return false
    }
    // Immediate first check + interval
    checkResult()
    const interval = setInterval(async () => {
      if (await checkResult()) clearInterval(interval)
    }, 2000)
    return () => clearInterval(interval)
  },[simId, pendingActionId, countryId, actionType])

  return (
    <div className="p-3 rounded-lg border bg-warning/5 border-warning/20">
      <div className="flex items-center gap-2">
        <div className="w-4 h-4 border-2 border-warning border-t-transparent rounded-full animate-spin"/>
        <h3 className="font-body text-caption font-medium text-warning uppercase">Awaiting Moderator</h3>
      </div>
    </div>
  )
}

export function AttackForm({roleId,countryId,simId,onClose,onSubmitted}:{
  roleId:string;countryId:string;simId:string;onClose:()=>void;onSubmitted:()=>void
}) {
  const [step,setStep]=useState<AttackStep>('select_source')
  const [sourceHex,setSourceHex]=useState<{row:number;col:number;theater?:string;theater_row?:number;theater_col?:number}|null>(null)
  const [sourceUnits,setSourceUnits]=useState<{unit_id:string;unit_type:string;status?:string}[]>([])
  const [selectedUnits,setSelectedUnits]=useState<string[]>([])
  const [targets,setTargets]=useState<AttackTarget[]>([])
  const [selectedTarget,setSelectedTarget]=useState<AttackTarget|null>(null)
  const [selectedEnemyUnit,setSelectedEnemyUnit]=useState<string|null>(null)
  const [attackType,setAttackType]=useState<string|null>(null)
  const [unitsUsedThisRound,setUnitsUsedThisRound]=useState<Set<string>>(new Set())
  const [submitting,setSubmitting]=useState(false)
  const [result,setResult]=useState<Record<string,unknown>|null>(null)
  const [missileTarget,setMissileTarget]=useState<string>('military')
  const [error,setError]=useState<string|null>(null)
  const [preview,setPreview]=useState<{win_probability:number;modifiers:{attacker:{label:string;value:unknown}[];defender:{label:string;value:unknown}[]};attacker:{units:number;modifier_total:number};defender:{units:number;modifier_total:number};has_air_defense:boolean}|null>(null)
  const mapRef = useRef<HTMLIFrameElement>(null)

  // Load units that already attacked this round (naval/air: once per round)
  // Also includes pending (submitted but not yet resolved) attacks
  const loadUsedUnits = useCallback(async ()=>{
    const {data:sr} = await supabase.from('sim_runs').select('current_round').eq('id',simId).limit(1)
    const round = sr?.[0]?.current_round ?? 0
    const used = new Set<string>()
    // CANONICAL: attacker_unit_codes is always a string[] in all combat payloads
    // Legacy keys checked for backward compatibility with older events
    const extractUnits = (pl: Record<string,unknown>): string[] => {
      const codes = pl.attacker_unit_codes as string[] | undefined
      if (codes?.length) return codes
      // Legacy fallback
      const singular = pl.attacker_unit_code as string | undefined
      if (singular) return [singular]
      const naval = pl.naval_unit_codes as string[] | undefined
      if (naval?.length) return naval
      return []
    }
    // From resolved events
    const {data:evts} = await supabase.from('observatory_events').select('payload')
      .eq('sim_run_id',simId).eq('round_num',round).eq('country_code',countryId)
      .in('event_type',['naval_combat','naval_bombardment','air_strike'])
    for (const evt of evts??[]) {
      const action = (evt.payload as Record<string,unknown>)?.action as Record<string,unknown> || {}
      extractUnits(action).forEach(c => used.add(c))
    }
    // From pending actions (submitted, not yet resolved)
    const {data:pa} = await supabase.from('pending_actions').select('payload')
      .eq('sim_run_id',simId).eq('country_code',countryId).eq('round_num',round)
      .in('action_type',['naval_combat','naval_bombardment','air_strike'])
      .in('status',['pending','approved'])
    for (const p of pa??[]) {
      extractUnits(p.payload as Record<string,unknown> || {}).forEach(c => used.add(c))
    }
    setUnitsUsedThisRound(used)
  },[simId,countryId])
  useEffect(()=>{ loadUsedUnits() },[loadUsedUnits])

  // Listen for postMessage from map iframe
  useEffect(()=>{
    const handler = (event: MessageEvent) => {
      const msg = event.data
      if (!msg || msg.type !== 'hex-click') return

      // Helper: try to select a new source hex from any step
      const trySelectSource = () => {
        const myUnits = (msg.units || []).filter((u:{country_code:string})=>u.country_code===countryId)
        if (myUnits.length === 0) return false
        const combatUnits = myUnits.filter((u:{unit_type:string;status?:string})=>
          ['ground','tactical_air','naval','strategic_missile'].includes(u.unit_type)
        )
        if (combatUnits.length === 0) return false

        // Reset all state and select new source
        setSourceHex({row:msg.row,col:msg.col,
          theater:msg.theater||undefined,theater_row:msg.theater_row||undefined,theater_col:msg.theater_col||undefined})
        setSourceUnits(combatUnits)
        setSelectedUnits([])
        setTargets([]); setSelectedTarget(null); setSelectedEnemyUnit(null)
        setAttackType(null); setError(null); setPreview(null)
        setStep('select_units')
        mapRef.current?.contentWindow?.postMessage({type:'clear-highlights'},'*')
        mapRef.current?.contentWindow?.postMessage({type:'highlight-hexes',hexes:[{
          row:msg.row,col:msg.col,
          theater:msg.theater,theater_row:msg.theater_row,theater_col:msg.theater_col,
        }],style:'source'},'*')
        return true
      }

      if (step === 'select_source') {
        trySelectSource()
        return
      }

      if (step === 'select_units' || step === 'select_target' || step === 'confirm') {
        // If clicking a hex with own combat units → re-select source
        const myUnits = (msg.units || []).filter((u:{country_code:string})=>u.country_code===countryId)
        const hasCombat = myUnits.some((u:{unit_type:string})=>
          ['ground','tactical_air','naval','strategic_missile'].includes(u.unit_type)
        )
        if (hasCombat) {
          trySelectSource()
          return
        }

        // In select_target: check if clicked hex is a valid target
        if (step === 'select_target') {
          const match = targets.find(t=>t.row===msg.row && t.col===msg.col)
          if (!match) return
          setSelectedTarget(match)
          setAttackType(match.attack_type)
          // Reset missile target choice if nuclear_site not available on new hex
          if (missileTarget === 'nuclear_site' && !(match as Record<string,unknown>).has_nuclear_site) {
            setMissileTarget('military')
          }
          fetchPreview(match.attack_type, match.row, match.col)
          if (match.attack_type === 'naval_combat' && match.enemies.length > 1) {
            setStep('confirm')
          } else if (match.attack_type === 'naval_combat' && match.enemies.length === 1) {
            setSelectedEnemyUnit(match.enemies[0].unit_id)
            setStep('confirm')
          } else {
            setStep('confirm')
          }
        }
      }
    }
    window.addEventListener('message',handler)
    return ()=>window.removeEventListener('message',handler)
  },[step,countryId,targets])

  // When units are selected, fetch valid targets
  const [loadingTargets, setLoadingTargets] = useState(false)
  const handleUnitsSelected = async (unitIds: string[]) => {
    setSelectedUnits(unitIds)
    if (unitIds.length === 0) return

    // Use the first selected unit to get targets (all same type at same hex)
    const primaryUnit = unitIds[0]
    setError(null)
    setLoadingTargets(true)
    try {
      const token = await getToken()
      const theaterParam = sourceHex?.theater ? `&theater=${encodeURIComponent(sourceHex.theater)}` : ''
      const resp = await fetch(`${API_BASE}/api/sim/${simId}/attack/valid-targets?unit_id=${encodeURIComponent(primaryUnit)}${theaterParam}`,{
        headers: token ? {'Authorization':`Bearer ${token}`} : {},
      })
      if (!resp.ok) {
        const errData = await resp.json().catch(() => ({}))
        setError(errData.detail || `Server error ${resp.status}`)
        return
      }
      const data = await resp.json()

      setTargets(data.targets || [])
      if (data.units_attacked_this_round?.length) {
        setUnitsUsedThisRound(new Set(data.units_attacked_this_round))
      }
      setStep('select_target')

      // Highlight valid target hexes on map (include theater coords for theater view)
      const targetHexes = (data.targets || []).map((t:Record<string,unknown>)=>({
        row:t.row,col:t.col,
        theater:t.theater||null,theater_row:t.theater_row||null,theater_col:t.theater_col||null,
      }))
      mapRef.current?.contentWindow?.postMessage({type:'highlight-hexes',hexes:targetHexes,style:'target'},'*')

      if (targetHexes.length === 0) {
        setError('No valid targets in range')
      } else {
        setError(null)
      }
    } catch(e) {
      setError(e instanceof Error ? e.message : 'Failed to load targets')
    } finally {
      setLoadingTargets(false)
    }
  }

  const fetchPreview = async (aType: string, tRow: number, tCol: number) => {
    setPreview(null)
    try {
      const token = await getToken()
      const resp = await fetch(
        `/api/sim/${simId}/attack/preview?attacker_unit_ids=${encodeURIComponent(selectedUnits.join(','))}&target_row=${tRow}&target_col=${tCol}&attack_type=${aType}`,
        {headers: token ? {'Authorization':`Bearer ${token}`} : {}},
      )
      if (resp.ok) setPreview(await resp.json())
    } catch { /* preview is optional */ }
  }

  const handleSubmit = async () => {
    if (!selectedTarget || !attackType || selectedUnits.length === 0) return
    setSubmitting(true); setError(null)

    const params: Record<string,unknown> = {
      target_row: selectedTarget.row,
      target_col: selectedTarget.col,
    }

    // CANONICAL: every combat action sends attacker_unit_codes, source hex, and theater info
    let actionType = attackType
    params.attacker_unit_codes = selectedUnits
    params.source_global_row = sourceHex?.row
    params.source_global_col = sourceHex?.col
    // Theater info: if attack was initiated from a theater map, include theater coords
    // This tells the dispatcher to resolve combat in theater coordinate space
    if (sourceHex?.theater) {
      params.theater = sourceHex.theater
      params.source_theater_row = sourceHex.theater_row
      params.source_theater_col = sourceHex.theater_col
      if (selectedTarget?.theater_row) {
        params.target_theater_row = selectedTarget.theater_row
        params.target_theater_col = selectedTarget.theater_col
      }
    }
    // Missile: target choice
    if (attackType === 'launch_missile_conventional') {
      params.target_choice = missileTarget
    }
    // Naval combat: target ship
    if (attackType === 'naval_combat' && selectedEnemyUnit) {
      params.target_unit_code = selectedEnemyUnit
    }

    try {
      const res = await submitAction(simId, actionType, roleId, countryId, params)
      if (res.status === 'pending' || res.status === 'awaiting_dice') {
        // Attack queued for moderator — don't show as result
        setResult({...res, pending: true})
        setStep('result')
      } else {
        setResult(res)
        setStep('result')
        // Refresh map to show losses
        mapRef.current?.contentWindow?.postMessage({type:'refresh-units'},'*')
      }
      mapRef.current?.contentWindow?.postMessage({type:'clear-highlights'},'*')
    } catch(e) {
      setError(e instanceof Error ? e.message : 'Attack failed')
    } finally {
      setSubmitting(false)
    }
  }

  const resetToSource = () => {
    setStep('select_source')
    setSourceHex(null); setSourceUnits([]); setSelectedUnits([])
    setTargets([]); setSelectedTarget(null); setSelectedEnemyUnit(null)
    setAttackType(null); setError(null); setResult(null); setPreview(null)
    mapRef.current?.contentWindow?.postMessage({type:'clear-highlights'},'*')
    loadUsedUnits() // refresh used-units list after attacking
  }

  // Determine which unit types can be selected at source hex
  const unitsByType: Record<string,{unit_id:string;unit_type:string}[]> = {}
  sourceUnits.forEach(u => {
    unitsByType[u.unit_type] = unitsByType[u.unit_type] || []
    unitsByType[u.unit_type].push(u)
  })

  return (
    <div className="flex gap-3" style={{height:'calc(100vh - 180px)'}}>
      {/* LEFT SIDEBAR — controls (1/3) */}
      <div className="w-1/4 min-w-[240px] flex flex-col gap-2 overflow-y-auto pr-1">
        {/* Header */}
        <div className="flex items-center justify-between">
          <h2 className="font-heading text-h3 text-text-primary">Attack</h2>
          <div className="flex gap-1">
            {step !== 'select_source' && step !== 'result' && (
              <button onClick={resetToSource}
                className="font-body text-caption text-text-secondary hover:text-text-primary px-2 py-0.5 rounded border border-border">
                Reset
              </button>
            )}
            <button onClick={onClose}
              className="font-body text-caption text-text-secondary hover:text-text-primary px-2 py-0.5 rounded border border-border">
              ← Back
            </button>
          </div>
        </div>

        {/* Step indicator */}
        <div className="flex gap-1 text-caption font-body flex-wrap">
          {(['select_source','select_units','select_target','confirm'] as AttackStep[]).map((s,i)=>(
            <div key={s} className={`flex items-center gap-0.5 ${step===s?'text-action font-medium':
              (['select_source','select_units','select_target','confirm'].indexOf(step)>i?'text-success':'text-text-secondary/50')}`}>
              <span className={`w-4 h-4 rounded-full flex items-center justify-center text-xs border ${
                step===s?'border-action bg-action/10':
                (['select_source','select_units','select_target','confirm'].indexOf(step)>i?'border-success bg-success/10':'border-border')
              }`}>{i+1}</span>
              <span className="text-xs">{s==='select_source'?'Hex':s==='select_units'?'Units':s==='select_target'?'Target':'Go'}</span>
              {i<3&&<span className="text-text-secondary/30">→</span>}
            </div>
          ))}
        </div>

        {/* Step content */}
        <div className="bg-card border border-border rounded-lg p-3 min-h-[60px] flex-1">
        {step === 'select_source' && (
          <p className="font-body text-body-sm text-text-secondary">
            Click a hex on the map that contains your military units.
          </p>
        )}

        {step === 'select_units' && (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <p className="font-body text-caption text-text-secondary">
                Source: hex ({sourceHex?.row},{sourceHex?.col}) — select unit(s) to attack with
              </p>
              <button onClick={()=>{setStep('select_source');setSourceHex(null);setSourceUnits([]);setSelectedUnits([]);mapRef.current?.contentWindow?.postMessage({type:'clear-highlights'},'*')}}
                className="font-body text-caption text-text-secondary hover:text-action">← Change hex</button>
            </div>
            {Object.entries(unitsByType).map(([type, units]) => (
              <div key={type} className="space-y-1">
                <h4 className="font-body text-caption text-text-secondary uppercase tracking-wider">
                  {UNIT_TYPE_LABELS[type]??type} ({units.length})
                </h4>
                {type === 'ground' ? (
                  /* Ground: multi-select, max 3, must leave 1 behind */
                  <div className="flex flex-wrap gap-2 items-center">
                    {(()=>{
                      const groundCount = units.length
                      const maxSelect = Math.min(3, Math.max(1, groundCount - 1))
                      const selectedGround = selectedUnits.filter(x=>sourceUnits.find(s=>s.unit_id===x)?.unit_type==='ground').length
                      return <>
                        {units.map(u => {
                          const sel = selectedUnits.includes(u.unit_id)
                          return <button key={u.unit_id} onClick={()=>{
                            if (sel) setSelectedUnits(prev=>prev.filter(x=>x!==u.unit_id))
                            else if (selectedGround < maxSelect)
                              setSelectedUnits(prev=>[...prev,u.unit_id])
                          }}
                            title={u.unit_id}
                            className={`inline-flex items-center justify-center w-10 h-10 rounded border-2 transition-colors ${
                              sel?'bg-action/10 border-action text-action':
                              selectedGround >= maxSelect?'border-border/30 text-text-secondary/30 cursor-not-allowed':
                              'border-border text-text-secondary hover:border-action/30 hover:text-action'
                            }`}>
                            <UnitIcon type={type} size={24} />
                          </button>
                        })}
                        <span className="font-body text-caption text-text-secondary/50">
                          {selectedGround}/{maxSelect}{groundCount > 1 && <span className="text-text-secondary/30 ml-1">(1 stays)</span>}
                        </span>
                      </>
                    })()}
                  </div>
                ) : (
                  /* Others: single select — naval/air disabled if already attacked this round */
                  <div className="flex flex-wrap gap-2 items-center">
                    {units.map(u => {
                      const sel = selectedUnits.includes(u.unit_id)
                      const used = unitsUsedThisRound.has(u.unit_id)
                      return <button key={u.unit_id} onClick={()=>{
                        if (!used) setSelectedUnits([u.unit_id])
                      }}
                        title={used ? `${u.unit_id} — already attacked this round` : u.unit_id}
                        disabled={used}
                        className={`inline-flex items-center justify-center w-10 h-10 rounded border-2 transition-colors ${
                          used?'border-border/20 text-text-secondary/20 cursor-not-allowed opacity-40':
                          sel?'bg-action/10 border-action text-action':'border-border text-text-secondary hover:border-action/30 hover:text-action'
                        }`}>
                        <UnitIcon type={type} size={24} />
                        {u.status==='embarked'&&<span className="text-xs absolute -bottom-1 -right-1">⚓</span>}
                      </button>
                    })}
                  </div>
                )}
              </div>
            ))}
            {selectedUnits.length > 0 && (
              <button onClick={()=>handleUnitsSelected(selectedUnits)} disabled={loadingTargets}
                className="font-body text-caption font-medium px-4 py-2 rounded bg-action/10 text-action border border-action/30 hover:bg-action/20 transition-colors disabled:opacity-50">
                {loadingTargets ? 'Loading...' : 'Find Targets →'}
              </button>
            )}
          </div>
        )}

        {step === 'select_target' && (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <p className="font-body text-body-sm text-text-secondary">
                {targets.length > 0
                  ? <>Click a <span className="text-danger font-medium">highlighted hex</span> on the map to select your target. {targets.length} valid target{targets.length>1?'s':''}.</>
                  : 'No valid targets in range.'
                }
              </p>
              <button onClick={()=>{setStep('select_units');setTargets([]);setSelectedTarget(null);mapRef.current?.contentWindow?.postMessage({type:'clear-highlights'},'*');mapRef.current?.contentWindow?.postMessage({type:'highlight-hexes',hexes:[sourceHex!],style:'source'},'*')}}
                className="font-body text-caption text-text-secondary hover:text-action">← Change units</button>
            </div>
            {/* Target list as backup (in case map click is tricky) */}
          </div>
        )}

        {step === 'confirm' && selectedTarget && (
          <div className="space-y-3">
            <div className="flex justify-end">
              <button onClick={()=>{setStep('select_target');setSelectedTarget(null);setSelectedEnemyUnit(null);setAttackType(null)}}
                className="font-body text-caption text-text-secondary hover:text-action">← Change target</button>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <span className="font-body text-caption text-text-secondary block">Attack Type</span>
                <span className="font-body text-body-sm text-text-primary font-medium">
                  {ATTACK_TYPE_LABELS[attackType??'']??attackType}
                </span>
              </div>
              <div>
                <span className="font-body text-caption text-text-secondary block">Target</span>
                <span className="font-data text-body-sm text-danger">
                  ({selectedTarget.row},{selectedTarget.col})
                </span>
              </div>
              <div>
                <span className="font-body text-caption text-text-secondary block">Our Units</span>
                <div className="flex gap-1 flex-wrap mt-0.5">
                  {selectedUnits.map(uid=>{
                    const utype = sourceUnits.find(s=>s.unit_id===uid)?.unit_type||'ground'
                    return <span key={uid} title={uid} className="text-action"><UnitIcon type={utype} size={20}/></span>
                  })}
                </div>
              </div>
              <div>
                <span className="font-body text-caption text-text-secondary block">Enemy Units</span>
                <div className="flex gap-1 flex-wrap mt-0.5">
                  {selectedTarget.enemies.map(e=>
                    <span key={e.unit_id} title={`${e.unit_id} (${e.country_code})`} className="text-danger"><UnitIcon type={e.unit_type} size={20}/></span>
                  )}
                </div>
              </div>
            </div>

            {/* Combat preview: modifiers + win probability */}
            {preview && (
              <div className="bg-base border border-border rounded-lg p-3 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-body text-caption text-text-secondary uppercase tracking-wider">Combat Assessment</span>
                </div>
                <div className="flex gap-0.5">
                  {[15,30,45,60,75].map(t =>
                    <div key={t} className="w-3 h-3 rounded-sm border" style={{
                      borderColor: '#1A5276',
                      backgroundColor: preview.win_probability >= t ? '#1A5276' : 'transparent',
                    }}/>
                  )}
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <span className="font-body text-caption text-action font-medium block">
                      Attacker {preview.attacker.modifier_total !== 0 && (
                        <span className={preview.attacker.modifier_total > 0 ? 'text-success' : 'text-danger'}>
                          ({preview.attacker.modifier_total > 0 ? '+' : ''}{preview.attacker.modifier_total})
                        </span>
                      )}
                    </span>
                    {preview.modifiers.attacker.length > 0 ? preview.modifiers.attacker.map((m,i) => (
                      <div key={i} className="font-body text-caption text-text-secondary">
                        {m.label}: <span className={typeof m.value === 'number' ? (m.value as number) > 0 ? 'text-success' : 'text-danger' : 'text-text-primary'}>{typeof m.value === 'number' ? (m.value > 0 ? `+${m.value}` : m.value) : m.value}</span>
                      </div>
                    )) : <div className="font-body text-caption text-text-secondary/50">No modifiers</div>}
                  </div>
                  <div>
                    <span className="font-body text-caption text-danger font-medium block">
                      Defender {preview.defender.modifier_total !== 0 && (
                        <span className={preview.defender.modifier_total > 0 ? 'text-success' : 'text-danger'}>
                          ({preview.defender.modifier_total > 0 ? '+' : ''}{preview.defender.modifier_total})
                        </span>
                      )}
                    </span>
                    {preview.modifiers.defender.length > 0 ? preview.modifiers.defender.map((m,i) => (
                      <div key={i} className="font-body text-caption text-text-secondary">
                        {m.label}: <span className={typeof m.value === 'number' ? (m.value as number) > 0 ? 'text-success' : 'text-danger' : 'text-text-primary'}>{typeof m.value === 'number' ? (m.value > 0 ? `+${m.value}` : m.value) : m.value}</span>
                      </div>
                    )) : <div className="font-body text-caption text-text-secondary/50">No modifiers</div>}
                  </div>
                </div>
              </div>
            )}

            {/* Naval combat: pick specific target ship */}
            {attackType === 'naval_combat' && selectedTarget.enemies.length > 1 && (
              <div>
                <span className="font-body text-caption text-text-secondary block mb-1">Select enemy ship:</span>
                <div className="flex gap-2">
                  {selectedTarget.enemies.map(e=>(
                    <button key={e.unit_id} onClick={()=>setSelectedEnemyUnit(e.unit_id)}
                      title={`${e.unit_id} (${e.country_code})`}
                      className={`inline-flex items-center justify-center w-10 h-10 rounded border-2 transition-colors ${
                        selectedEnemyUnit===e.unit_id?'bg-danger/10 border-danger text-danger':'border-border text-text-secondary hover:border-danger/30'
                      }`}>
                      <UnitIcon type="naval" size={24}/>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Missile: target choice */}
            {attackType === 'launch_missile_conventional' && (
              <div>
                <span className="font-body text-caption text-text-secondary block mb-1">Target:</span>
                <div className="flex flex-col gap-1">
                  {([
                    {v:'military',l:'Military unit'},
                    {v:'infrastructure',l:'Infrastructure (-2% GDP)'},
                    ...((selectedTarget as Record<string,unknown>)?.has_nuclear_site ? [{v:'nuclear_site' as const,l:'Nuclear site (halve R&D)'}] : []),
                    {v:'ad',l:'Air defense unit'},
                  ]).map(o=>
                    <label key={o.v} className="flex items-center gap-2 font-body text-caption cursor-pointer">
                      <input type="radio" name="missile_target" value={o.v} checked={missileTarget===o.v}
                        onChange={()=>setMissileTarget(o.v)}
                        className="accent-action" />
                      <span className={missileTarget===o.v?'text-text-primary':'text-text-secondary'}>{o.l}</span>
                    </label>
                  )}
                </div>
              </div>
            )}

            <div className="flex gap-3 pt-2">
              <button onClick={handleSubmit}
                disabled={submitting || (attackType==='naval_combat' && !selectedEnemyUnit)}
                className="font-body text-caption font-bold uppercase px-5 py-2 rounded bg-danger text-white hover:bg-danger/80 transition-colors disabled:opacity-50">
                {submitting ? 'Executing...' : 'Confirm Attack'}
              </button>
              <button onClick={resetToSource}
                className="font-body text-caption px-4 py-2 rounded border border-border text-text-secondary hover:text-text-primary">
                Cancel
              </button>
            </div>
          </div>
        )}

        {step === 'result' && result && (
          <div className="space-y-3">
            {result.pending ? (
              <PendingResultPoller simId={simId} pendingActionId={result.pending_action_id as string|undefined}
                countryId={countryId} actionType={attackType??'ground_attack'} onResolved={(res)=>{
                setResult(res); mapRef.current?.contentWindow?.postMessage({type:'refresh-units'},'*')
              }} />
            ) : (
              <div className={`p-3 rounded-lg border ${result.attacker_won ? 'bg-success/5 border-success/20' : 'bg-danger/5 border-danger/20'}`}>
                <h3 className={`font-body text-body-sm font-bold uppercase ${result.attacker_won ? 'text-success' : 'text-danger'}`}>
                  {attackType === 'naval_bombardment'
                    ? (result.attacker_won ? 'Target Hit' : 'No Targets Hit')
                    : attackType === 'air_strike'
                    ? (result.attacker_won ? 'Target Hit' : 'Missed')
                    : attackType === 'launch_missile_conventional'
                    ? (result.attacker_won ? 'Impact' : 'Missed')
                    : attackType === 'ground_move'
                    ? 'Advanced'
                    : (result.attacker_won ? 'Victory' : 'Defeat')}
                </h3>
              </div>
            )}

            {/* Casualties — icons with cross overlay */}
            {((result.attacker_losses as string[]||[]).length > 0 || (result.defender_losses as string[]||[]).length > 0) && (
              <div className="space-y-2">
                {(result.attacker_losses as string[]||[]).length > 0 && (
                  <div className="flex items-center gap-1 flex-wrap">
                    <span className="font-body text-caption text-text-secondary mr-1">Our losses:</span>
                    {(result.attacker_losses as string[]).map((uid,i)=>
                      <span key={i} title={uid} className="relative inline-block text-action">
                        <UnitIcon type={attackType==='naval_combat'?'naval':attackType==='air_strike'?'tactical_air':attackType==='launch_missile_conventional'?'strategic_missile':'ground'} size={22}/>
                        <span className="absolute inset-0 flex items-center justify-center text-danger font-bold text-lg leading-none">✕</span>
                      </span>
                    )}
                  </div>
                )}
                {(result.defender_losses as string[]||[]).length > 0 && (
                  <div className="flex items-center gap-1 flex-wrap">
                    <span className="font-body text-caption text-text-secondary mr-1">Enemy losses:</span>
                    {(result.defender_losses as string[]).map((uid,i)=>{
                      // Infer unit type from unit_id convention: _g_=ground, _a_=tactical_air, _d_=air_defense, _n_=naval, _m_=strategic_missile
                      const inferType = (id:string) => {
                        if (id.includes('_a_') || id.includes('_a0')) return 'tactical_air'
                        if (id.includes('_d_') || id.includes('_d0')) return 'air_defense'
                        if (id.includes('_n_') || id.includes('_n0') || id.includes('_nr')) return 'naval'
                        if (id.includes('_m_') || id.includes('_m0')) return 'strategic_missile'
                        return 'ground'
                      }
                      return <span key={i} title={uid} className="relative inline-block text-danger">
                        <UnitIcon type={inferType(uid)} size={22}/>
                        <span className="absolute inset-0 flex items-center justify-center text-danger font-bold text-lg leading-none">✕</span>
                      </span>
                    })}
                  </div>
                )}
              </div>
            )}

            {/* Captured trophies */}
            {(result.captured as {unit_id:string;type:string;from:string}[]||[]).length > 0 && (
              <div className="flex items-center gap-1 flex-wrap">
                <span className="font-body text-caption text-text-secondary mr-1">Captured:</span>
                {(result.captured as {unit_id:string;type:string;from:string}[]).map((c,i)=>
                  <span key={i} title={`${c.unit_id} (${c.type} from ${c.from})`} className="relative inline-block text-action">
                    <UnitIcon type={c.type} size={22}/>
                  </span>
                )}
                <span className="font-body text-caption text-action/60 ml-1">→ reserve</span>
              </div>
            )}

            <div className="flex gap-2">
              <button onClick={resetToSource}
                className="font-body text-caption px-3 py-1.5 rounded bg-action/10 text-action border border-action/30 hover:bg-action/20">
                Attack Again
              </button>
              <button onClick={onSubmitted}
                className="font-body text-caption px-3 py-1.5 rounded border border-border text-text-secondary hover:text-text-primary">
                ← Done
              </button>
            </div>
          </div>
        )}
      </div>

        {error && step !== 'result' && (
          <div className="bg-danger/5 border border-danger/20 rounded-lg p-3">
            <p className="font-body text-body-sm text-danger">{error}</p>
          </div>
        )}
      </div>

      {/* RIGHT — Map (3/4), always visible */}
      <div className="flex-1 flex flex-col gap-1">
        <div className="flex gap-1">
          {(['global','eastern_ereb','mashriq'] as const).map(v=>(
            <button key={v} onClick={()=>mapRef.current?.contentWindow?.postMessage({type:'navigate-theater',theater:v==='global'?'global':v},'*')}
              className="font-body text-caption px-2 py-0.5 rounded border border-border text-text-secondary hover:border-action/30 hover:text-action transition-colors">
              {v==='global'?'Global':v==='eastern_ereb'?'E. Ereb':'Mashriq'}
            </button>
          ))}
        </div>
        <div className="relative flex-1 rounded-lg overflow-hidden border border-border">
          <iframe
            ref={mapRef}
            src={`/map/deployments.html?display=clean&mode=attack&country=${countryId}&sim_run_id=${simId}`}
            className="absolute inset-0 w-full h-full border-0"
            title="Attack Map"
          />
        </div>
      </div>
    </div>
  )
}

/* ── Move Units Form ───────────────────────────────────────────────────── */

interface QueuedMove {
  unit_code: string
  unit_type: string
  target: string
  target_global_row?: number
  target_global_col?: number
  label: string
}

export function SetMeetingsForm({roleId,countryId,simId,onClose,onSubmitted}:{
  roleId:string;countryId:string;simId:string;onClose:()=>void;onSubmitted:()=>void
}) {
  const [loading, setLoading] = useState(true)
  const [meetingType, setMeetingType] = useState<'one_on_one'|'organization'>('one_on_one')
  const [allRoles, setAllRoles] = useState<{id:string;character_name:string;country_code:string}[]>([])
  const [myOrgs, setMyOrgs] = useState<{id:string;name:string}[]>([])
  const [countries, setCountries] = useState<{id:string;sim_name:string;color_ui:string}[]>([])
  const [targetRole, setTargetRole] = useState('')
  const [targetOrg, setTargetOrg] = useState('')
  const [message, setMessage] = useState('')
  const [theme, setTheme] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState<string|null>(null)
  const [error, setError] = useState<string|null>(null)

  // Realtime: my outgoing invitations
  const { data: myOutgoingRaw } = useRealtimeTable<Record<string, unknown>>(
    'meeting_invitations', simId,
    { eq: { inviter_role_id: roleId } },
  )
  const myOutgoing = (myOutgoingRaw as unknown as {
    id:string; invitation_type:string; invitee_role_id:string|null; org_id:string|null; org_name:string|null;
    message:string; status:string; expires_at:string; responses:Record<string, {response:string; message?:string}>;
  }[]).filter(inv => inv.status === 'pending' && new Date(inv.expires_at).getTime() > Date.now())

  useEffect(() => {
    if (!simId || !countryId || !roleId) { setLoading(false); return }
    let cancelled = false
    // Safety: force loading off after 5s no matter what
    const timeout = setTimeout(() => { if (!cancelled) setLoading(false) }, 5000)
    setLoading(true)
    Promise.all([
      supabase.from('roles').select('id,character_name,country_code')
        .eq('sim_run_id', simId).eq('status', 'active'),
      supabase.from('org_memberships').select('org_id')
        .eq('sim_run_id', simId).eq('country_code', countryId),
      supabase.from('organizations').select('id,sim_name')
        .eq('sim_run_id', simId),
      supabase.from('countries').select('id,sim_name,color_ui')
        .eq('sim_run_id', simId).order('sim_name'),
    ]).then(([rolesRes, memsRes, orgsRes, countriesRes]) => {
      if (cancelled) return
      if (rolesRes.data) setAllRoles(rolesRes.data.filter((r: Record<string,unknown>) => r.id !== roleId) as typeof allRoles)
      if (countriesRes.data) setCountries(countriesRes.data as typeof countries)
      const myOrgIds = new Set((memsRes.data || []).map((m: Record<string,unknown>) => m.org_id as string))
      const orgMap = (orgsRes.data || []) as {id:string;sim_name:string}[]
      setMyOrgs(orgMap.filter(o => myOrgIds.has(o.id)).map(o => ({ id: o.id, name: o.sim_name || o.id })))
    }).catch(err => console.error('SetMeetingsForm load failed:', err))
    .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true; clearTimeout(timeout) }
  }, [simId, countryId, roleId])

  const handleSubmit = async () => {
    if (meetingType === 'one_on_one' && !targetRole) return
    if (meetingType === 'organization' && !targetOrg) return
    setSubmitting(true); setError(null); setResult(null)
    try {
      const params: Record<string, string> = {
        invitation_type: meetingType,
        message: message.trim(),
      }
      if (meetingType === 'one_on_one') {
        params.invitee_role_id = targetRole
      } else {
        params.org_id = targetOrg
        params.org_name = myOrgs.find(o => o.id === targetOrg)?.name || targetOrg
        params.theme = theme.trim()
      }
      const res = await submitAction(simId, 'invite_to_meet', roleId, countryId, params)
      if (res.success) {
        setResult(res.narrative || 'Invitation sent')
        setMessage(''); setTheme(''); setTargetRole(''); setTargetOrg('')
      } else {
        setError(res.narrative || 'Failed')
      }
    } catch (e) { setError(e instanceof Error ? e.message : 'Failed') }
    finally { setSubmitting(false) }
  }

  if (loading) return <div className="p-4 text-text-secondary">Loading...</div>

  // Group roles by country
  const byCountry = countries.map(c => ({
    ...c,
    roles: allRoles.filter(r => r.country_code === c.id),
  })).filter(c => c.roles.length > 0)

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="font-heading text-h2 text-text-primary">Set Meetings</h2>
        <button onClick={onClose}
          className="font-body text-caption text-text-secondary hover:text-text-primary px-3 py-1 rounded border border-border">
          ← Back
        </button>
      </div>

      {/* Type toggle */}
      <div className="flex gap-2">
        <button onClick={() => setMeetingType('one_on_one')}
          className={`flex-1 font-body text-body-sm py-2 rounded-lg border transition-colors ${
            meetingType === 'one_on_one' ? 'border-action bg-action/10 text-action font-medium' : 'border-border text-text-secondary'
          }`}>1:1 Meeting</button>
        {myOrgs.length > 0 && (
          <button onClick={() => setMeetingType('organization')}
            className={`flex-1 font-body text-body-sm py-2 rounded-lg border transition-colors ${
              meetingType === 'organization' ? 'border-action bg-action/10 text-action font-medium' : 'border-border text-text-secondary'
            }`}>Organization Meeting</button>
        )}
      </div>

      {/* Outgoing invitations with responses */}
      {myOutgoing.length > 0 && (
        <div className="space-y-2">
          <label className="font-body text-caption text-text-secondary">Your active invitations</label>
          {myOutgoing.map(inv => (
              <div key={inv.id} className="relative bg-card border border-action/20 rounded-lg p-3">
                <div className="font-body text-caption text-text-primary font-medium">
                  {inv.invitation_type === 'one_on_one'
                    ? `To: ${inv.invitee_role_id}`
                    : `${inv.org_name || inv.org_id} meeting`}
                </div>
                <div className="font-body text-caption text-text-secondary/50 mt-1">Awaiting response...</div>
                <button
                  onClick={async () => {
                    await supabase.from('meeting_invitations').update({ status: 'cancelled' }).eq('id', inv.id)
                  }}
                  className="absolute top-2 right-2 text-text-secondary/40 hover:text-danger p-1 transition-colors"
                  title="Cancel invitation"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M18 6 6 18M6 6l12 12"/>
                  </svg>
                </button>
              </div>
          ))}
        </div>
      )}

      {result ? (
        <div className="bg-success/5 border border-success/20 rounded-lg p-4">
          <p className="font-body text-body-sm text-success font-medium">{result}</p>
          <button onClick={() => setResult(null)}
            className="font-body text-caption text-action hover:underline mt-2">
            Send another invitation
          </button>
        </div>
      ) : (
        <>
          {meetingType === 'one_on_one' ? (
            <>
              <div>
                <label className="font-body text-caption text-text-secondary block mb-2">Invite</label>
                <div className="bg-card border border-border rounded-lg divide-y divide-border max-h-[300px] overflow-y-auto">
                  {byCountry.map(c => (
                    <div key={c.id}>
                      <div className="flex items-center gap-2 px-3 py-1.5 bg-base">
                        <div className="w-2.5 h-2.5 rounded" style={{backgroundColor: c.color_ui || '#666'}} />
                        <span className="font-body text-caption text-text-secondary font-medium uppercase tracking-wider">{c.sim_name}</span>
                      </div>
                      {c.roles.map(r => (
                        <label key={r.id} className={`flex items-center gap-3 px-4 py-2 cursor-pointer transition-colors ${
                          targetRole === r.id ? 'bg-action/5' : 'hover:bg-base'
                        }`}>
                          <input type="radio" name="invite_role" value={r.id} checked={targetRole === r.id}
                            onChange={() => setTargetRole(r.id)} className="accent-action"/>
                          <span className="font-body text-body-sm text-text-primary">{r.character_name}</span>
                        </label>
                      ))}
                    </div>
                  ))}
                </div>
              </div>
              <div>
                <label className="font-body text-caption text-text-secondary block mb-2">
                  Message <span className="text-text-secondary/50">(optional, max 300 chars)</span>
                </label>
                <textarea value={message} onChange={e => setMessage(e.target.value.slice(0, 300))}
                  placeholder="I'd like to discuss..."
                  rows={2}
                  className="w-full bg-base border border-border rounded-lg px-4 py-2 font-body text-body-sm text-text-primary resize-none focus:border-action/50 focus:outline-none transition-colors"
                />
              </div>
            </>
          ) : (
            <>
              <div>
                <label className="font-body text-caption text-text-secondary block mb-2">Organization</label>
                <div className="bg-card border border-border rounded-lg divide-y divide-border">
                  {myOrgs.map(org => (
                    <label key={org.id} className={`flex items-center gap-3 px-4 py-2.5 cursor-pointer transition-colors ${
                      targetOrg === org.id ? 'bg-action/5' : 'hover:bg-base'
                    }`}>
                      <input type="radio" name="invite_org" value={org.id} checked={targetOrg === org.id}
                        onChange={() => setTargetOrg(org.id)} className="accent-action"/>
                      <span className="font-body text-body-sm text-text-primary">{org.name}</span>
                    </label>
                  ))}
                </div>
              </div>
              <div>
                <label className="font-body text-caption text-text-secondary block mb-2">Theme</label>
                <input value={theme} onChange={e => setTheme(e.target.value)}
                  placeholder="Agenda topic..."
                  className="w-full bg-base border border-border rounded-lg px-4 py-2 font-body text-body-sm text-text-primary focus:border-action/50 focus:outline-none transition-colors"
                />
              </div>
              <div>
                <label className="font-body text-caption text-text-secondary block mb-2">
                  Message <span className="text-text-secondary/50">(optional)</span>
                </label>
                <textarea value={message} onChange={e => setMessage(e.target.value.slice(0, 300))}
                  placeholder="Additional details..."
                  rows={2}
                  className="w-full bg-base border border-border rounded-lg px-4 py-2 font-body text-body-sm text-text-primary resize-none focus:border-action/50 focus:outline-none transition-colors"
                />
              </div>
            </>
          )}

          <button onClick={handleSubmit}
            disabled={submitting || (meetingType === 'one_on_one' ? !targetRole : !targetOrg)}
            className="w-full bg-action text-white font-body text-body-sm font-medium py-2.5 rounded-lg hover:bg-action/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
            {submitting ? 'Sending...' : meetingType === 'one_on_one' ? 'Send Invitation' : 'Send to All Members'}
          </button>
        </>
      )}

      {error && (
        <div className="bg-danger/5 border border-danger/20 rounded-lg p-4">
          <p className="font-body text-body-sm text-danger">{error}</p>
        </div>
      )}
    </div>
  )
}

export function IntelligenceForm({roleId,countryId,simId,onClose,onSubmitted}:{
  roleId:string;countryId:string;simId:string;onClose:()=>void;onSubmitted:()=>void
}) {
  const [question, setQuestion] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string|null>(null)
  const [success, setSuccess] = useState<string|null>(null)
  const [remaining, setRemaining] = useState<number|null>(null)

  useEffect(() => {
    supabase.from('role_actions').select('uses_remaining')
      .eq('sim_run_id', simId).eq('role_id', roleId).eq('action_id', 'intelligence').limit(1)
      .then(({ data }) => setRemaining(data?.[0]?.uses_remaining ?? null))
  }, [simId, roleId])

  const handleSubmit = async () => {
    if (question.trim().length < 10) return
    setSubmitting(true); setError(null); setSuccess(null)
    try {
      const res = await submitAction(simId, 'intelligence', roleId, countryId, {
        question: question.trim(),
      })
      if (res.success === false) {
        setError(res.narrative || res.message || 'Failed')
      } else {
        setSuccess('Intelligence report delivered. Switch to the Confidential tab to read it.')
        setQuestion('')
        if (remaining !== null && remaining > 0) setRemaining(remaining - 1)
        onSubmitted()  // triggers loadData which refreshes artefacts
      }
    } catch (e) { setError(e instanceof Error ? e.message : 'Failed') }
    finally { setSubmitting(false) }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="font-heading text-h2 text-text-primary">Intelligence</h2>
        <button onClick={onClose}
          className="font-body text-caption text-text-secondary hover:text-text-primary px-3 py-1 rounded border border-border">
          ← Back
        </button>
      </div>

      <div className="bg-action/5 border border-action/20 rounded-lg p-4">
        <p className="font-body text-body-sm text-text-primary">
          Submit a question to your intelligence services. You will receive a classified briefing in your Confidential tab.
        </p>
        <p className="font-body text-caption text-text-secondary mt-1">
          Intelligence reports are based on available information and may contain inaccuracies.
        </p>
        {remaining !== null && (
          <p className={`font-data text-caption mt-2 ${remaining > 0 ? 'text-text-secondary' : 'text-danger'}`}>
            {remaining > 0 ? `${remaining} request${remaining !== 1 ? 's' : ''} remaining this simulation` : 'No requests remaining'}
          </p>
        )}
      </div>

      {remaining === 0 ? (
        <div className="bg-danger/5 border border-danger/20 rounded-lg p-4 text-center">
          <p className="font-body text-body-sm text-danger font-medium">All intelligence requests have been used.</p>
        </div>
      ) : success ? (
        <div className="bg-success/5 border border-success/20 rounded-lg p-4">
          <p className="font-body text-body-sm text-success font-medium">{success}</p>
          <button onClick={() => setSuccess(null)}
            className="font-body text-caption text-action hover:underline mt-2">
            Submit another request
          </button>
        </div>
      ) : (
        <>
          <div>
            <label className="font-body text-caption text-text-secondary block mb-2">
              Your question <span className="text-text-secondary/50">(min 10 characters)</span>
            </label>
            <textarea value={question} onChange={e => setQuestion(e.target.value)}
              placeholder="What is the current state of Persia's nuclear program? How close are they to a weapon?"
              rows={4}
              className="w-full bg-base border border-border rounded-lg px-4 py-3 font-body text-body-sm text-text-primary resize-none focus:border-action/50 focus:outline-none transition-colors"
              disabled={submitting}
            />
          </div>

          <button onClick={handleSubmit} disabled={question.trim().length < 10 || submitting || remaining === 0}
            className="w-full bg-action text-white font-body text-body-sm font-medium py-2.5 rounded-lg hover:bg-action/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
            {submitting ? 'Generating report...' : 'Request Intelligence Report'}
          </button>
        </>
      )}

      {error && (
        <div className="bg-danger/5 border border-danger/20 rounded-lg p-4">
          <p className="font-body text-body-sm text-danger">{error}</p>
        </div>
      )}
    </div>
  )
}

export function CovertOpsForm({roleId,countryId,simId,onClose,onSubmitted}:{
  roleId:string;countryId:string;simId:string;onClose:()=>void;onSubmitted:()=>void
}) {
  const [loading, setLoading] = useState(true)
  const [countries, setCountries] = useState<{id:string;sim_name:string;color_ui:string}[]>([])
  const [opType, setOpType] = useState<'sabotage'|'propaganda'>('sabotage')
  const [targetCountry, setTargetCountry] = useState('')
  const [sabotageTarget, setSabotageTarget] = useState<'infrastructure'|'nuclear_tech'|'military'>('infrastructure')
  const [propagandaIntent, setPropagandaIntent] = useState<'boost'|'destabilize'>('destabilize')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string|null>(null)
  const [result, setResult] = useState<Record<string,unknown>|null>(null)
  const [remaining, setRemaining] = useState<number|null>(null)

  useEffect(() => {
    if (!simId || !roleId) { setLoading(false); return }
    let cancelled = false
    const timeout = setTimeout(() => { if (!cancelled) setLoading(false) }, 5000)
    setLoading(true)
    Promise.all([
      supabase.from('countries').select('id,sim_name,color_ui').eq('sim_run_id', simId).order('sim_name'),
      supabase.from('role_actions').select('uses_remaining')
        .eq('sim_run_id', simId).eq('role_id', roleId).eq('action_id', 'covert_operation').limit(1),
    ]).then(([countriesRes, usageRes]) => {
      if (cancelled) return
      if (countriesRes.data) setCountries(countriesRes.data as typeof countries)
      setRemaining(usageRes.data?.[0]?.uses_remaining ?? null)
    }).catch(err => console.error('CovertOpsForm load failed:', err))
    .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true; clearTimeout(timeout) }
  }, [simId, roleId])

  const handleSubmit = async () => {
    if (!targetCountry) return
    setSubmitting(true); setError(null); setResult(null)
    try {
      const params: Record<string, string> = {
        op_type: opType,
        target_country: targetCountry,
      }
      if (opType === 'sabotage') params.target_type = sabotageTarget
      if (opType === 'propaganda') params.intent = propagandaIntent

      const res = await submitAction(simId, 'covert_operation', roleId, countryId, params)
      if (res.success === false) {
        setError(res.narrative || 'Operation failed')
      } else {
        setResult(res)
        if (remaining !== null && remaining > 0) setRemaining(remaining - 1)
      }
    } catch (e) { setError(e instanceof Error ? e.message : 'Failed') }
    finally { setSubmitting(false) }
  }

  if (loading) return <div className="p-4 text-text-secondary">Loading...</div>

  const SABOTAGE_TARGETS = [
    { id: 'infrastructure' as const, label: 'Infrastructure' },
    { id: 'nuclear_tech' as const, label: 'Nuclear Site' },
    { id: 'military' as const, label: 'Military' },
  ]

  // For sabotage: exclude own country. For propaganda: include own (own first).
  const targetOptions = opType === 'sabotage'
    ? countries.filter(c => c.id !== countryId)
    : [...countries.filter(c => c.id === countryId), ...countries.filter(c => c.id !== countryId)]

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="font-heading text-h2 text-text-primary">Covert Operation</h2>
        <button onClick={onClose}
          className="font-body text-caption text-text-secondary hover:text-text-primary px-3 py-1 rounded border border-border">
          ← Back
        </button>
      </div>

      <div className="bg-text-secondary/5 border border-border rounded-lg p-4">
        <p className="font-body text-body-sm text-text-primary">
          Conduct a covert operation. Success is not guaranteed. Operations may be detected and attributed.
        </p>
        {remaining !== null && (
          <p className={`font-data text-caption mt-2 ${remaining > 0 ? 'text-text-secondary' : 'text-danger'}`}>
            {remaining > 0 ? `${remaining} operation${remaining !== 1 ? 's' : ''} remaining this simulation` : 'No operations remaining'}
          </p>
        )}
      </div>

      {remaining === 0 ? (
        <div className="bg-danger/5 border border-danger/20 rounded-lg p-4 text-center">
          <p className="font-body text-body-sm text-danger font-medium">All covert operations have been used.</p>
        </div>
      ) : result ? (
        <div className={`border rounded-lg p-4 ${result.success ? 'bg-success/5 border-success/20' : 'bg-danger/5 border-danger/20'}`}>
          <p className={`font-body text-body-sm font-medium ${result.success ? 'text-success' : 'text-danger'}`}>
            {result.success ? 'Operation Successful' : 'Operation Failed'}
          </p>
          <p className="font-body text-caption text-text-primary mt-1">{result.narrative as string}</p>
          {result.detected && (
            <p className="font-body text-caption text-warning mt-1">
              {result.attributed ? 'Operation was detected and attributed to your country.' : 'Operation was detected but attribution unclear.'}
            </p>
          )}
          <button onClick={() => { setResult(null); setTargetCountry('') }}
            className="font-body text-caption text-action hover:underline mt-2">
            Plan another operation
          </button>
        </div>
      ) : (
        <>
          {/* Op type selector */}
          <div>
            <label className="font-body text-caption text-text-secondary block mb-2">Operation type</label>
            <div className="flex gap-2">
              <button onClick={() => { setOpType('sabotage'); setTargetCountry('') }}
                className={`flex-1 font-body text-body-sm py-2 rounded-lg border transition-colors ${
                  opType === 'sabotage' ? 'border-action bg-action/10 text-action font-medium' : 'border-border text-text-secondary hover:border-action/30'
                }`}>Sabotage</button>
              <button onClick={() => { setOpType('propaganda'); setTargetCountry('') }}
                className={`flex-1 font-body text-body-sm py-2 rounded-lg border transition-colors ${
                  opType === 'propaganda' ? 'border-action bg-action/10 text-action font-medium' : 'border-border text-text-secondary hover:border-action/30'
                }`}>Propaganda</button>
            </div>
          </div>

          {/* Sabotage-specific: target type */}
          {opType === 'sabotage' && (
            <div>
              <label className="font-body text-caption text-text-secondary block mb-2">Sabotage target</label>
              <div className="bg-card border border-border rounded-lg divide-y divide-border">
                {SABOTAGE_TARGETS.map(t => (
                  <label key={t.id} className={`flex items-center gap-3 px-4 py-2.5 cursor-pointer transition-colors ${
                    sabotageTarget === t.id ? 'bg-action/5' : 'hover:bg-base'
                  }`}>
                    <input type="radio" name="sabotage_target" value={t.id} checked={sabotageTarget === t.id}
                      onChange={() => setSabotageTarget(t.id)} className="accent-action"/>
                    <div>
                      <span className="font-body text-body-sm text-text-primary">{t.label}</span>
                    </div>
                  </label>
                ))}
              </div>
            </div>
          )}

          {/* Propaganda-specific: intent */}
          {opType === 'propaganda' && (
            <div>
              <label className="font-body text-caption text-text-secondary block mb-2">Intent</label>
              <div className="flex gap-2">
                <button onClick={() => setPropagandaIntent('boost')}
                  className={`flex-1 font-body text-caption py-2 rounded border transition-colors ${
                    propagandaIntent === 'boost' ? 'border-success bg-success/10 text-success font-medium' : 'border-border text-text-secondary'
                  }`}>Support stability</button>
                <button onClick={() => setPropagandaIntent('destabilize')}
                  className={`flex-1 font-body text-caption py-2 rounded border transition-colors ${
                    propagandaIntent === 'destabilize' ? 'border-danger bg-danger/10 text-danger font-medium' : 'border-border text-text-secondary'
                  }`}>Undermine stability</button>
              </div>
            </div>
          )}

          {/* Target country */}
          <div>
            <label className="font-body text-caption text-text-secondary block mb-2">Target country</label>
            <div className="bg-card border border-border rounded-lg divide-y divide-border max-h-[300px] overflow-y-auto">
              {targetOptions.map(c => (
                <label key={c.id} className={`flex items-center gap-3 px-4 py-2 cursor-pointer transition-colors ${
                  targetCountry === c.id ? 'bg-action/5' : 'hover:bg-base'
                }`}>
                  <input type="radio" name="covert_target_country" value={c.id} checked={targetCountry === c.id}
                    onChange={() => setTargetCountry(c.id)} className="accent-action"/>
                  <div className="w-2.5 h-2.5 rounded" style={{backgroundColor: c.color_ui || '#666'}} />
                  <span className="font-body text-body-sm text-text-primary">{c.sim_name}</span>
                  {c.id === countryId && <span className="font-body text-caption text-text-secondary ml-auto">(your country)</span>}
                </label>
              ))}
            </div>
          </div>

          <button onClick={handleSubmit} disabled={!targetCountry || submitting || remaining === 0}
            className="w-full bg-action text-white font-body text-body-sm font-medium py-2.5 rounded-lg hover:bg-action/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
            {submitting ? 'Executing...' : `Execute ${opType === 'sabotage' ? 'Sabotage' : 'Propaganda'}`}
          </button>
        </>
      )}

      {error && (
        <div className="bg-danger/5 border border-danger/20 rounded-lg p-4">
          <p className="font-body text-body-sm text-danger">{error}</p>
        </div>
      )}
    </div>
  )
}

export function AssassinationForm({roleId,countryId,simId,onClose,onSubmitted}:{
  roleId:string;countryId:string;simId:string;onClose:()=>void;onSubmitted:()=>void
}) {
  const [loading, setLoading] = useState(true)
  const [allRoles, setAllRoles] = useState<{id:string;character_name:string;country_code:string;positions:string[];status:string}[]>([])
  const [countries, setCountries] = useState<{id:string;sim_name:string;color_ui:string}[]>([])
  const [targetId, setTargetId] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string|null>(null)
  const [result, setResult] = useState<{narrative:string;killed:boolean;attributed:boolean}|null>(null)
  const [remaining, setRemaining] = useState<number|null>(null)
  const [pendingId, setPendingId] = useState<string|null>(null)

  useEffect(() => {
    if (!simId || !roleId) { setLoading(false); return }
    let cancelled = false
    const timeout = setTimeout(() => { if (!cancelled) setLoading(false) }, 5000)
    setLoading(true)
    Promise.all([
      supabase.from('roles').select('id,character_name,country_code,positions,status')
        .eq('sim_run_id', simId).eq('status', 'active'),
      supabase.from('countries').select('id,sim_name,color_ui')
        .eq('sim_run_id', simId).order('sim_name'),
      supabase.from('role_actions').select('uses_remaining')
        .eq('sim_run_id', simId).eq('role_id', roleId).eq('action_id', 'assassination').limit(1),
    ]).then(([rolesRes, countriesRes, usageRes]) => {
      if (cancelled) return
      if (rolesRes.data) setAllRoles(rolesRes.data as typeof allRoles)
      if (countriesRes.data) setCountries(countriesRes.data as typeof countries)
      setRemaining(usageRes.data?.[0]?.uses_remaining ?? null)
    }).catch(err => console.error('AssassinationForm load failed:', err))
    .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true; clearTimeout(timeout) }
  }, [simId, countryId, roleId])

  // Group targets by country (exclude self)
  const targets = allRoles.filter(r => r.id !== roleId)
  const byCountry = countries.map(c => ({
    ...c,
    roles: targets.filter(r => r.country_code === c.id),
  })).filter(c => c.roles.length > 0)

  const handleSubmit = async () => {
    if (!targetId) return
    const targetRole = targets.find(r => r.id === targetId)
    if (!confirm(`Attempt assassination of ${targetRole?.character_name}?\n\nSuccess is not guaranteed. There is a chance the operation will be disclosed.\n\nThis will be sent to the moderator for confirmation.`)) return
    setSubmitting(true); setError(null)
    try {
      const res = await submitAction(simId, 'assassination', roleId, countryId, {
        changes: { target_role: targetId },
      })
      if (res.status === 'pending') {
        setPendingId(res.pending_action_id || null)
        setResult({ narrative: 'Assassination order submitted — awaiting moderator confirmation', killed: false, attributed: false })
      } else if (res.success !== false) {
        setResult({ narrative: res.narrative || 'Operation executed', killed: res.killed || false, attributed: res.attributed || false })
        if (remaining !== null) setRemaining(Math.max(0, remaining - 1))
      } else {
        setError(res.narrative || 'Failed')
      }
    } catch (e) { setError(e instanceof Error ? e.message : 'Failed') }
    finally { setSubmitting(false) }
  }

  if (loading) return <div className="p-4 text-text-secondary">Loading...</div>

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="font-heading text-h2 text-text-primary">Assassination</h2>
        <button onClick={onClose}
          className="font-body text-caption text-text-secondary hover:text-text-primary px-3 py-1 rounded border border-border">
          ← Back
        </button>
      </div>

      <div className="bg-danger/5 border border-danger/20 rounded-lg p-4">
        <p className="font-body text-body-sm text-text-primary">
          Order an assassination of any active participant. Success is <strong className="text-danger">not guaranteed</strong>, and there is a chance the operation will be disclosed.
        </p>
        {remaining !== null && (
          <p className={`font-data text-caption mt-2 ${remaining > 0 ? 'text-text-secondary' : 'text-danger'}`}>
            {remaining > 0 ? `${remaining} attempt${remaining !== 1 ? 's' : ''} remaining this simulation` : 'No attempts remaining'}
          </p>
        )}
      </div>

      {remaining === 0 ? (
        <div className="bg-danger/5 border border-danger/20 rounded-lg p-4 text-center">
          <p className="font-body text-body-sm text-danger font-medium">All assassination attempts have been used.</p>
        </div>
      ) : result ? (
        <div className="space-y-3">
          <div className={`${result.killed ? 'bg-danger/5 border-danger/20' : 'bg-action/5 border-action/20'} border rounded-lg p-4`}>
            <p className="font-body text-body-sm text-text-primary">{result.narrative}</p>
          </div>
          {pendingId && !result.killed && !result.attributed && (
            <PendingResultPoller simId={simId} pendingActionId={pendingId} countryId={countryId} actionType="assassination"
              onResolved={(res) => {
                const r = res as Record<string, unknown>
                const narrative = (r.narrative as string) || 'Operation complete'
                setResult({ narrative, killed: r.killed === true, attributed: r.attributed === true })
                setPendingId(null)
                if (remaining !== null) setRemaining(Math.max(0, remaining - 1))
              }} />
          )}
        </div>
      ) : (
        <>
          <div>
            <label className="font-body text-caption text-text-secondary block mb-2">Select target</label>
            <div className="bg-card border border-border rounded-lg divide-y divide-border max-h-[400px] overflow-y-auto">
              {byCountry.map(c => (
                <div key={c.id}>
                  <div className="flex items-center gap-2 px-3 py-1.5 bg-base">
                    <div className="w-2.5 h-2.5 rounded" style={{backgroundColor: c.color_ui || '#666'}} />
                    <span className="font-body text-caption text-text-secondary font-medium uppercase tracking-wider">{c.sim_name}</span>
                  </div>
                  {c.roles.map(r => (
                    <label key={r.id} className={`flex items-center gap-3 px-4 py-2 cursor-pointer transition-colors ${
                      targetId === r.id ? 'bg-danger/5' : 'hover:bg-base'
                    }`}>
                      <input type="radio" name="assassination_target" value={r.id} checked={targetId === r.id}
                        onChange={() => setTargetId(r.id)} className="accent-danger"/>
                      <span className="font-body text-body-sm text-text-primary flex-1">{r.character_name}</span>
                      <span className="font-body text-caption text-text-secondary">
                        {(r.positions || []).length > 0 ? (r.positions || []).map(p => POS[p] ?? p).join(' + ') : 'Citizen'}
                      </span>
                    </label>
                  ))}
                </div>
              ))}
            </div>
          </div>

          <button onClick={handleSubmit} disabled={!targetId || submitting || remaining === 0}
            className="w-full bg-danger text-white font-body text-body-sm font-medium py-2.5 rounded-lg hover:bg-danger/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
            {submitting ? 'Submitting...' : targetId ? `Order Assassination of ${targets.find(r=>r.id===targetId)?.character_name}` : 'Select a target'}
          </button>
        </>
      )}

      {error && (
        <div className="bg-danger/5 border border-danger/20 rounded-lg p-4">
          <p className="font-body text-body-sm text-danger">{error}</p>
        </div>
      )}
    </div>
  )
}

export function ArrestForm({roleId,countryId,simId,onClose,onSubmitted}:{
  roleId:string;countryId:string;simId:string;onClose:()=>void;onSubmitted:()=>void
}) {
  const [loading, setLoading] = useState(true)
  const [roles, setRoles] = useState<{id:string;character_name:string;positions:string[];status:string}[]>([])
  const [targetId, setTargetId] = useState('')
  const [justification, setJustification] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string|null>(null)
  const [success, setSuccess] = useState<string|null>(null)
  const [remaining, setRemaining] = useState<number|null>(null)

  const loadRoles = useCallback(() => {
    if (!simId || !countryId || !roleId) { setLoading(false); return () => {} }
    let cancelled = false
    const timeout = setTimeout(() => { if (!cancelled) setLoading(false) }, 5000)
    setLoading(true)
    Promise.all([
      supabase.from('roles').select('id,character_name,positions,status')
        .eq('sim_run_id', simId).eq('country_code', countryId).in('status', ['active', 'arrested']),
      supabase.from('role_actions').select('uses_remaining')
        .eq('sim_run_id', simId).eq('role_id', roleId).eq('action_id', 'arrest').limit(1),
    ]).then(([rolesRes, usageRes]) => {
      if (cancelled) return
      if (rolesRes.data) setRoles(rolesRes.data as typeof roles)
      setRemaining(usageRes.data?.[0]?.uses_remaining ?? null)
    }).catch(err => console.error('ArrestForm load failed:', err))
    .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true; clearTimeout(timeout) }
  }, [simId, countryId, roleId])

  useEffect(() => { return loadRoles() }, [loadRoles])

  // Arrest targets: active, not self, not HoS
  const targets = roles.filter(r => r.id !== roleId && r.status === 'active' && !(r.positions || []).includes('head_of_state'))
  // Currently arrested in this country
  const arrested = roles.filter(r => r.status === 'arrested')

  const handleRelease = async (targetId: string, name: string) => {
    if (!confirm(`Release ${name} from arrest?`)) return
    setSubmitting(true); setError(null); setSuccess(null)
    try {
      const res = await submitAction(simId, 'release_arrest', roleId, countryId, {
        changes: { target_role: targetId },
      })
      if (res.success) {
        setSuccess(res.message || `${name} released`)
        // Optimistic update — move from arrested to active immediately
        setRoles(prev => prev.map(r => r.id === targetId ? { ...r, status: 'active' } : r))
      } else {
        setError(res.message || res.narrative || 'Failed')
      }
    } catch (e) { setError(e instanceof Error ? e.message : 'Failed') }
    finally { setSubmitting(false) }
  }

  const handleSubmit = async () => {
    if (!targetId || justification.trim().length < 30) return
    if (!confirm(`Arrest ${targets.find(r=>r.id===targetId)?.character_name}?\n\nThis will be sent to the moderator for confirmation.`)) return
    setSubmitting(true); setError(null)
    try {
      const res = await submitAction(simId, 'arrest', roleId, countryId, {
        changes: { target_role: targetId },
        rationale: justification.trim(),
      })
      if (res.status === 'pending') {
        setSuccess('Arrest request submitted — awaiting moderator confirmation')
      } else if (res.success) {
        setSuccess(res.narrative || 'Arrest executed')
      } else {
        setError(res.narrative || 'Failed')
      }
      onSubmitted()
    } catch (e) { setError(e instanceof Error ? e.message : 'Failed') }
    finally { setSubmitting(false) }
  }

  if (loading) return <div className="p-4 text-text-secondary">Loading...</div>

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="font-heading text-h2 text-text-primary">Arrest</h2>
        <button onClick={onClose}
          className="font-body text-caption text-text-secondary hover:text-text-primary px-3 py-1 rounded border border-border">
          ← Back
        </button>
      </div>

      <div className="bg-danger/5 border border-danger/20 rounded-lg p-4">
        <p className="font-body text-body-sm text-text-primary">
          Arrest a citizen of your country. The arrested person will be <strong className="text-danger">unable to take any actions</strong> for the remainder of this round. Released automatically at round end.
        </p>
        {remaining !== null && (
          <p className={`font-data text-caption mt-2 ${remaining > 0 ? 'text-text-secondary' : 'text-danger'}`}>
            {remaining > 0 ? `${remaining} arrest${remaining !== 1 ? 's' : ''} remaining this simulation` : 'No arrests remaining'}
          </p>
        )}
      </div>

      {/* Currently arrested — release option */}
      {arrested.length > 0 && (
        <div>
          <label className="font-body text-caption text-text-secondary block mb-2">Currently arrested</label>
          <div className="bg-card border border-danger/20 rounded-lg divide-y divide-border">
            {arrested.map(r => (
              <div key={r.id} className="flex items-center justify-between px-4 py-2.5">
                <span className="font-body text-body-sm text-danger font-medium">{r.character_name}</span>
                <button onClick={() => handleRelease(r.id, r.character_name)} disabled={submitting}
                  className="font-body text-caption font-medium bg-success/10 text-success px-3 py-1 rounded hover:bg-success/20 disabled:opacity-50 transition-colors">
                  Release
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {remaining === 0 && (
        <div className="bg-danger/5 border border-danger/20 rounded-lg p-4 text-center">
          <p className="font-body text-body-sm text-danger font-medium">All arrest actions have been used this simulation.</p>
        </div>
      )}

      {success ? (
        <div className="bg-success/5 border border-success/20 rounded-lg p-4">
          <p className="font-body text-body-sm text-success font-medium">{success}</p>
        </div>
      ) : (<>
        <div>
          <label className="font-body text-caption text-text-secondary block mb-2">Target</label>
          <div className="bg-card border border-border rounded-lg divide-y divide-border">
            {targets.map(r => (
              <label key={r.id} className={`flex items-center gap-3 px-4 py-2.5 cursor-pointer transition-colors ${
                targetId === r.id ? 'bg-danger/5' : 'hover:bg-base'
              }`}>
                <input type="radio" name="arrest_target" value={r.id} checked={targetId === r.id}
                  onChange={() => setTargetId(r.id)} className="accent-danger"/>
                <span className="font-body text-body-sm text-text-primary flex-1">{r.character_name}</span>
                <span className="font-body text-caption text-text-secondary">
                  {(r.positions || []).length > 0 ? (r.positions || []).map(p => POS[p] ?? p).join(' + ') : 'Citizen'}
                </span>
              </label>
            ))}
          </div>
        </div>

        <div>
          <label className="font-body text-caption text-text-secondary block mb-2">
            Justification <span className="text-text-secondary/50">(min 30 characters)</span>
          </label>
          <textarea value={justification} onChange={e => setJustification(e.target.value)}
            placeholder="Reason for the arrest..."
            rows={3}
            className="w-full bg-base border border-border rounded-lg px-4 py-3 font-body text-body-sm text-text-primary resize-none focus:border-action/50 focus:outline-none transition-colors"
          />
          {justification.length > 0 && justification.length < 30 && (
            <span className="font-body text-caption text-warning mt-1 block">{30 - justification.length} more characters needed</span>
          )}
        </div>

        <button onClick={handleSubmit} disabled={!targetId || justification.trim().length < 30 || submitting || remaining === 0}
          className="w-full bg-danger text-white font-body text-body-sm font-medium py-2.5 rounded-lg hover:bg-danger/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
          {submitting ? 'Submitting...' : targetId ? `Arrest ${targets.find(r=>r.id===targetId)?.character_name}` : 'Select a target'}
        </button>
      </>)}

      {error && (
        <div className="bg-danger/5 border border-danger/20 rounded-lg p-4">
          <p className="font-body text-body-sm text-danger">{error}</p>
        </div>
      )}
    </div>
  )
}

export function ReassignPowersForm({roleId,countryId,simId,onClose,onSubmitted}:{
  roleId:string;countryId:string;simId:string;onClose:()=>void;onSubmitted:()=>void
}) {
  const [loading, setLoading] = useState(true)
  const [roles, setRoles] = useState<{id:string;character_name:string;positions:string[];title:string}[]>([])
  const [selectedPosition, setSelectedPosition] = useState<string>('')
  const [targetRoleId, setTargetRoleId] = useState<string>('')
  const [vacate, setVacate] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string|null>(null)
  const [success, setSuccess] = useState<string|null>(null)

  const POSITIONS = [
    { id: 'military', label: 'Military' },
    { id: 'economy', label: 'Economy' },
    { id: 'diplomat', label: 'Diplomat' },
    { id: 'security', label: 'Security' },
  ]

  useEffect(() => {
    if (!simId || !countryId) { setLoading(false); return }
    let cancelled = false
    const timeout = setTimeout(() => { if (!cancelled) setLoading(false) }, 5000)
    setLoading(true)
    supabase.from('roles').select('id,character_name,positions,title')
      .eq('sim_run_id', simId).eq('country_code', countryId).eq('status', 'active')
      .then(({ data }) => {
        if (cancelled) return
        if (data) setRoles(data as typeof roles)
      }).catch(err => console.error('ReassignForm load failed:', err))
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true; clearTimeout(timeout) }
  }, [simId, countryId])

  // Who currently holds the selected position?
  const currentHolder = selectedPosition
    ? roles.find(r => (r.positions || []).includes(selectedPosition))
    : null

  // Eligible targets: all roles except the current holder
  const eligibleTargets = roles.filter(r => r.id !== currentHolder?.id)

  const handleSubmit = async () => {
    if (!selectedPosition) return
    const target = vacate ? null : targetRoleId || null
    if (!vacate && !target) return

    setSubmitting(true); setError(null)
    try {
      const res = await submitAction(simId, 'reassign_types', roleId, countryId, {
        position: selectedPosition,
        target_role_id: target,
      })
      if (!res.success) { setError(res.narrative || 'Failed'); setSubmitting(false); return }
      setSuccess(res.narrative || 'Position reassigned')
      setSelectedPosition(''); setTargetRoleId(''); setVacate(false)
      // Reload roles to show updated positions — stay on same screen
      const { data } = await supabase.from('roles').select('id,character_name,positions,title')
        .eq('sim_run_id', simId).eq('country_code', countryId).eq('status', 'active')
      if (data) setRoles(data as typeof roles)
    } catch (e) { setError(e instanceof Error ? e.message : 'Failed') }
    finally { setSubmitting(false) }
  }

  if (loading) return <div className="p-4 text-text-secondary">Loading...</div>

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="font-heading text-h2 text-text-primary">Reassign Powers</h2>
        <button onClick={onClose}
          className="font-body text-caption text-text-secondary hover:text-text-primary px-3 py-1 rounded border border-border">
          ← Back
        </button>
      </div>

      {/* Current assignments overview */}
      <div className="bg-card border border-border rounded-lg divide-y divide-border">
        {POSITIONS.map(pos => {
          const holder = roles.find(r => (r.positions || []).includes(pos.id))
          return (
            <div key={pos.id} className="flex items-center gap-3 px-4 py-2.5">
              <span className="font-body text-body-sm text-text-secondary w-20 shrink-0">{pos.label}</span>
              <span className={`font-body text-body-sm ${holder ? 'text-text-primary font-medium' : 'text-text-secondary/50'}`}>
                {holder ? holder.character_name : 'Vacant'}
              </span>
            </div>
          )
        })}
      </div>

      {success && (
        <div className="bg-success/5 border border-success/20 rounded-lg p-4">
          <p className="font-body text-body-sm text-success font-medium">{success}</p>
        </div>
      )}

      {/* Select position to reassign */}
      <div>
        <label className="font-body text-caption text-text-secondary block mb-2">Position to reassign</label>
        <div className="flex flex-wrap gap-2">
          {POSITIONS.map(pos => (
            <button key={pos.id} onClick={() => { setSelectedPosition(pos.id); setTargetRoleId(''); setVacate(false); setSuccess(null) }}
              className={`font-body text-caption px-3 py-1.5 rounded border transition-colors ${
                selectedPosition === pos.id
                  ? 'border-action bg-action/10 text-action font-medium'
                  : 'border-border text-text-secondary hover:border-action/30'
              }`}>
              {pos.label}
            </button>
          ))}
        </div>
      </div>

      {selectedPosition && (
        <>
          {currentHolder && (
            <div className="font-body text-caption text-text-secondary">
              Currently held by <strong className="text-text-primary">{currentHolder.character_name}</strong>
            </div>
          )}

          {/* Assign to or vacate */}
          <div>
            <label className="font-body text-caption text-text-secondary block mb-2">
              {currentHolder ? 'Transfer to' : 'Assign to'}
            </label>
            <div className="bg-card border border-border rounded-lg divide-y divide-border">
              {eligibleTargets.map(r => (
                <label key={r.id} className={`flex items-center gap-3 px-4 py-2.5 cursor-pointer transition-colors ${
                  !vacate && targetRoleId === r.id ? 'bg-action/5' : 'hover:bg-base'
                }`}>
                  <input type="radio" name="target" value={r.id} checked={!vacate && targetRoleId === r.id}
                    onChange={() => { setTargetRoleId(r.id); setVacate(false) }} className="accent-action"/>
                  <span className="font-body text-body-sm text-text-primary flex-1">{r.character_name}</span>
                  <span className="font-body text-caption text-text-secondary">
                    {(r.positions || []).length > 0 ? (r.positions || []).map(p => POS[p] ?? p).join(' + ') : 'Citizen'}
                  </span>
                </label>
              ))}
              {currentHolder && (
                <label className={`flex items-center gap-3 px-4 py-2.5 cursor-pointer transition-colors ${
                  vacate ? 'bg-warning/5' : 'hover:bg-base'
                }`}>
                  <input type="radio" name="target" value="" checked={vacate}
                    onChange={() => { setVacate(true); setTargetRoleId('') }} className="accent-warning"/>
                  <span className="font-body text-body-sm text-warning">Vacate position</span>
                  <span className="font-body text-caption text-text-secondary">Remove without assigning</span>
                </label>
              )}
            </div>
          </div>

          <button onClick={handleSubmit} disabled={(!targetRoleId && !vacate) || submitting}
            className="w-full bg-action text-white font-body text-body-sm font-medium py-2.5 rounded-lg hover:bg-action/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
            {submitting ? 'Reassigning...'
              : vacate ? `Vacate ${POSITIONS.find(p=>p.id===selectedPosition)?.label}`
              : targetRoleId ? `Assign ${POSITIONS.find(p=>p.id===selectedPosition)?.label} to ${roles.find(r=>r.id===targetRoleId)?.character_name}`
              : 'Select a target'}
          </button>
        </>
      )}

      {error && (
        <div className="bg-danger/5 border border-danger/20 rounded-lg p-4">
          <p className="font-body text-body-sm text-danger">{error}</p>
        </div>
      )}
    </div>
  )
}

export function ChangeLeaderForm({roleId,countryId,simId,onClose,onSubmitted}:{
  roleId:string;countryId:string;simId:string;onClose:()=>void;onSubmitted:()=>void
}) {
  const [loading, setLoading] = useState(true)
  const [stability, setStability] = useState(10)
  const [hosName, setHosName] = useState('')
  const [isHosSelf, setIsHosSelf] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string|null>(null)
  const [success, setSuccess] = useState<string|null>(null)
  const threshold = 4.0

  useEffect(() => {
    if (!simId || !countryId) { setLoading(false); return }
    let cancelled = false
    const timeout = setTimeout(() => { if (!cancelled) setLoading(false) }, 5000)
    setLoading(true)
    Promise.all([
      supabase.from('countries').select('stability').eq('sim_run_id',simId).eq('id',countryId).limit(1),
      supabase.from('roles').select('id,character_name,positions').eq('sim_run_id',simId).eq('country_code',countryId).contains('positions',['head_of_state']).eq('status','active').limit(1),
    ]).then(([cs, rs]) => {
      if (cancelled) return
      setStability(cs.data?.[0]?.stability ?? 10)
      setHosName(rs.data?.[0]?.character_name ?? 'Unknown')
      setIsHosSelf(rs.data?.[0]?.id === roleId)
    }).catch(() => {
      if (!cancelled) setError('Failed to load — please retry')
    }).finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true; clearTimeout(timeout) }
  }, [simId, countryId, roleId])

  // HoS can resign without stability check; citizens need stability ≤ threshold
  const canInitiate = isHosSelf || stability <= threshold

  const handleInitiate = async () => {
    if (!canInitiate) return
    const msg = isHosSelf
      ? 'Resign from Head of State and initiate election of a new leader?\n\nThis cannot be undone.'
      : `Initiate removal of ${hosName} as Head of State?\n\nAll citizens will vote. This cannot be undone.`
    if (!confirm(msg)) return
    setSubmitting(true); setError(null)
    try {
      const res = await submitAction(simId, 'change_leader', roleId, countryId, {})
      if (!res.success) { setError(res.narrative || 'Failed'); setSubmitting(false); return }
      setSuccess(res.narrative || 'Vote initiated')
      onSubmitted()
    } catch (e) { setError(e instanceof Error ? e.message : 'Failed') }
    finally { setSubmitting(false) }
  }

  if (loading) return <div className="p-4 text-text-secondary">Loading...</div>

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="font-heading text-h2 text-text-primary">Change Leader</h2>
        <button onClick={onClose}
          className="font-body text-caption text-text-secondary hover:text-text-primary px-3 py-1 rounded border border-border">
          ← Back
        </button>
      </div>

      {isHosSelf ? (
        /* HoS voluntary resignation — no stability check, no removal vote */
        <div className="bg-action/5 border border-action/20 rounded-lg p-4">
          <p className="font-body text-body-sm text-text-primary">
            Resign from the position of Head of State and initiate election of a new leader.
            All citizens will vote to elect your successor.
          </p>
        </div>
      ) : (
        /* Citizen-initiated removal — requires stability check */
        <>
          <div className="bg-danger/5 border border-danger/20 rounded-lg p-4">
            <p className="font-body text-body-sm text-text-primary">
              Initiate removal of <strong className="text-danger">{hosName}</strong> as Head of State.
              All citizens will vote. Requires stability ≤ {threshold.toFixed(1)}.
            </p>
          </div>
          <div className="grid grid-cols-2 gap-3 text-center">
            <div className="bg-base rounded-lg p-3">
              <div className={`font-data text-data-lg ${canInitiate ? 'text-danger' : 'text-text-primary'}`}>
                {stability.toFixed(1)}
              </div>
              <div className="font-body text-caption text-text-secondary">Current stability</div>
            </div>
            <div className="bg-base rounded-lg p-3">
              <div className="font-data text-data-lg text-text-secondary">{threshold.toFixed(1)}</div>
              <div className="font-body text-caption text-text-secondary">Threshold</div>
            </div>
          </div>
        </>
      )}

      {success ? (
        <div className="bg-success/5 border border-success/20 rounded-lg p-4">
          <p className="font-body text-body-sm text-success font-medium">{success}</p>
          <p className="font-body text-caption text-text-secondary mt-1">
            Election is now open in Actions Expected Now for all citizens.
          </p>
        </div>
      ) : (
        <button onClick={handleInitiate} disabled={!canInitiate || submitting}
          className={`w-full font-body text-body-sm font-medium py-2.5 rounded-lg transition-colors ${
            canInitiate
              ? 'bg-action text-white hover:bg-action/90 cursor-pointer'
              : 'bg-base text-text-secondary/50 cursor-not-allowed'
          } disabled:opacity-50 disabled:cursor-not-allowed`}>
          {submitting ? 'Initiating...'
            : isHosSelf ? 'Resign and Initiate Election'
            : canInitiate ? 'Initiate Leadership Change'
            : `Stability too high (${stability.toFixed(1)} > ${threshold})`}
        </button>
      )}
      {error && (
        <div className="bg-danger/5 border border-danger/20 rounded-lg p-4">
          <p className="font-body text-body-sm text-danger">{error}</p>
        </div>
      )}
    </div>
  )
}

export function MoveUnitsForm({roleId,countryId,simId,onClose,onSubmitted}:{
  roleId:string;countryId:string;simId:string;onClose:()=>void;onSubmitted:()=>void
}) {
  type MoveEntry = {unit_id:string;unit_type:string;action:'deploy'|'withdraw';target_row?:number;target_col?:number;theater?:string;theater_row?:number;theater_col?:number}
  const [activeUnits,setActiveUnits]=useState<{unit_id:string;unit_type:string;global_row:number|null;global_col:number|null}[]>([])
  const [reserveUnits,setReserveUnits]=useState<{unit_id:string;unit_type:string}[]>([])
  const [embarkedUnits,setEmbarkedUnits]=useState<{unit_id:string;unit_type:string;embarked_on:string|null}[]>([])
  const [moves,setMoves]=useState<MoveEntry[]>([])
  const [mode,setMode]=useState<'withdraw'|'deploy'>('deploy')
  const [selectedUnit,setSelectedUnit]=useState<{unit_id:string;unit_type:string}|null>(null)
  const [hexUnits,setHexUnits]=useState<{unit_id:string;unit_type:string}[]>([]) // units at clicked hex for withdraw selection
  const [loading,setLoading]=useState(true)
  const [submitting,setSubmitting]=useState(false)
  const [result,setResult]=useState<Record<string,unknown>|null>(null)
  const [error,setError]=useState<string|null>(null)
  const [basingCountries,setBasingCountries]=useState<Set<string>>(new Set()) // countries where we have basing rights
  const mapRef = useRef<HTMLIFrameElement>(null)

  // Load basing rights
  useEffect(()=>{
    supabase.from('relationships').select('from_country_code,to_country_code,basing_rights_a_to_b,basing_rights_b_to_a')
      .eq('sim_run_id',simId)
      .or(`from_country_code.eq.${countryId},to_country_code.eq.${countryId}`)
      .then(({data})=>{
        const countries = new Set<string>()
        ;(data??[]).forEach((r:Record<string,unknown>)=>{
          // We receive basing FROM them
          if(r.from_country_code===countryId && r.basing_rights_b_to_a) countries.add(r.to_country_code as string)
          if(r.to_country_code===countryId && r.basing_rights_a_to_b) countries.add(r.from_country_code as string)
        })
        setBasingCountries(countries)
      })
  },[simId,countryId])

  const loadUnits = useCallback(async (signal?: {cancelled:boolean}) => {
    setLoading(true)
    try {
      const token = await getToken()
      const resp = await fetch(`${API_BASE}/api/sim/${simId}/units/my?country=${encodeURIComponent(countryId)}`, {
        headers: token ? {'Authorization':`Bearer ${token}`} : {},
      })
      if (!resp.ok) throw new Error('Failed to load units')
      const json = await resp.json()
      if (signal?.cancelled) return
      const data = json.data || json
      setActiveUnits(data.active ?? [])
      setReserveUnits(data.reserve ?? [])
      setEmbarkedUnits(data.embarked ?? [])
    } catch (e) { if (!signal?.cancelled) setError(e instanceof Error ? e.message : 'Failed') }
    finally { if (!signal?.cancelled) setLoading(false) }
  }, [simId, countryId])

  useEffect(() => {
    if (!simId || !countryId) { setLoading(false); return }
    const signal = {cancelled: false}
    const timeout = setTimeout(() => { if (!signal.cancelled) setLoading(false) }, 5000)
    loadUnits(signal)
    return () => { signal.cancelled = true; clearTimeout(timeout) }
  }, [loadUnits])

  // Effective reserve: original reserve + withdrawn units - deployed units
  // Effective reserve: original reserve (minus deployed) + withdrawn units, deduplicated
  const seen = new Set<string>()
  const effectiveReserve: {unit_id:string;unit_type:string}[] = []
  for (const u of reserveUnits) {
    if (!moves.some(m => m.unit_id === u.unit_id && m.action === 'deploy') && !seen.has(u.unit_id)) {
      effectiveReserve.push(u); seen.add(u.unit_id)
    }
  }
  for (const m of moves) {
    if (m.action === 'withdraw' && !seen.has(m.unit_id)) {
      effectiveReserve.push({unit_id: m.unit_id, unit_type: m.unit_type}); seen.add(m.unit_id)
    }
  }
  const reserveByType: Record<string, {unit_id:string;unit_type:string}[]> = {}
  effectiveReserve.forEach(u => {
    reserveByType[u.unit_type] = reserveByType[u.unit_type] || []
    reserveByType[u.unit_type].push(u)
  })

  // Send all pending moves to map for preview rendering
  const syncMapPreview = useCallback((newMoves: MoveEntry[]) => {
    mapRef.current?.contentWindow?.postMessage({
      type: 'preview-moves',
      moves: newMoves.map(m => ({
        unit_id: m.unit_id,
        unit_type: m.unit_type,
        action: m.action,
        target_row: m.target_row,
        target_col: m.target_col,
        theater: m.theater,
        theater_row: m.theater_row,
        theater_col: m.theater_col,
        country_code: countryId,
      })),
    }, '*')
  }, [countryId])

  // Hex click handler
  useEffect(() => {
    const handler = (event: MessageEvent) => {
      const msg = event.data
      if (!msg || msg.type !== 'hex-click') return
      const row = msg.row as number, col = msg.col as number

      // Territory check: hex owner must be own country, or has own units, or sea (naval only)
      const hexOwner = msg.owner as string || 'sea'
      const view = msg.view as string
      const theaterName = view !== 'global' ? view : undefined
      const theaterRow = msg.theater_row as number | undefined
      const theaterCol = msg.theater_col as number | undefined

      const tryDeploy = () => {
        if (!selectedUnit) return false
        if (moves.some(m => m.unit_id === selectedUnit.unit_id && m.action === 'deploy')) {
          setError('Unit already queued'); return true
        }
        // Validate territory: own territory, or hex with own units
        const isOwnTerritory = hexOwner === countryId
        const isSea = hexOwner === 'sea'
        const ownUnitsHere = (msg.units || []).filter((u:{country_code:string}) => u.country_code === countryId)
        const hasOwnUnits = ownUnitsHere.length > 0
        const isNaval = selectedUnit.unit_type === 'naval'
        const isLand = !isNaval
        // Check for friendly carrier at sea hex (ground: 1 per ship, air: 2 per ship)
        const ownNavalHere = ownUnitsHere.filter((u:{unit_type:string}) => u.unit_type === 'naval')
        const hasCarrier = ownNavalHere.length > 0

        const hasBasing = basingCountries.has(hexOwner)

        if (isSea && isLand && !hasCarrier) { setError('Land units need a carrier to deploy to sea'); return true }
        if (!isSea && isNaval) { setError('Naval units can only deploy to sea'); return true }
        if (!isOwnTerritory && !hasOwnUnits && !hasBasing && !isSea) { setError('Can only deploy to own territory, basing rights, or hexes with your units'); return true }

        const newMoves = [...moves, {
          unit_id: selectedUnit.unit_id, unit_type: selectedUnit.unit_type,
          action: 'deploy' as const, target_row: row, target_col: col,
          theater: theaterName, theater_row: theaterRow, theater_col: theaterCol,
        }]
        setMoves(newMoves)
        syncMapPreview(newMoves)
        setSelectedUnit(null); setHexUnits([]); setError(null)
        return true
      }

      if (selectedUnit && hexUnits.length === 0) {
        tryDeploy()
      } else {
        // Show own units at this hex for withdrawal
        const mapUnits = (msg.units || []).filter((u:{country_code:string}) => u.country_code === countryId)
        const afterWithdraw = mapUnits.filter((u:{unit_id:string}) => !moves.some(m => m.unit_id === u.unit_id && m.action === 'withdraw'))
        const deployedHere = moves.filter(m => m.action === 'deploy' && m.target_row === row && m.target_col === col)
          .map(m => ({unit_id: m.unit_id, unit_type: m.unit_type}))
        const allHere = [...afterWithdraw, ...deployedHere.filter(d => !afterWithdraw.some((u:{unit_id:string}) => u.unit_id === d.unit_id))]
        const available = allHere.filter(u => !moves.some(m => m.unit_id === u.unit_id))
        if (available.length > 0) {
          setHexUnits(available)
          setMode('withdraw')
        } else if (selectedUnit) {
          tryDeploy()
        }
      }
    }
    window.addEventListener('message', handler)
    return () => window.removeEventListener('message', handler)
  }, [mode, selectedUnit, moves, countryId, syncMapPreview])

  const withdrawUnit = (u: {unit_id:string;unit_type:string}) => {
    const newMoves = [...moves, {unit_id: u.unit_id, unit_type: u.unit_type, action: 'withdraw' as const}]
    setMoves(newMoves)
    const remaining = hexUnits.filter(x => x.unit_id !== u.unit_id)
    setHexUnits(remaining)
    syncMapPreview(newMoves)
    // Last withdrawn unit becomes ready for deployment
    setSelectedUnit({unit_id: u.unit_id, unit_type: u.unit_type})
    // Stay in withdraw mode if more units at this hex, otherwise switch to deploy
    if (remaining.length === 0) {
      setMode('deploy')
    }
  }

  const removeMove = (unitId: string) => {
    const newMoves = moves.filter(m => m.unit_id !== unitId)
    setMoves(newMoves)
    syncMapPreview(newMoves)
  }

  const discardAll = () => {
    setMoves([])
    setSelectedUnit(null)
    setHexUnits([])
    setError(null)
    // Restore map to original state
    mapRef.current?.contentWindow?.postMessage({type: 'preview-moves', moves: []}, '*')
  }

  const handleSubmit = async () => {
    if (moves.length === 0) return
    setSubmitting(true); setError(null)
    // Merge withdraw+deploy of same unit into single reposition move
    // withdraw-only = target:reserve, deploy-only = target:hex, both = target:hex (reposition)
    const withdraws = new Map(moves.filter(m => m.action === 'withdraw').map(m => [m.unit_id, m]))
    const deploys = new Map(moves.filter(m => m.action === 'deploy').map(m => [m.unit_id, m]))
    const payload: {unit_code:string;target:string;target_global_row?:number;target_global_col?:number}[] = []
    const seen = new Set<string>()
    for (const m of moves) {
      if (seen.has(m.unit_id)) continue
      seen.add(m.unit_id)
      const dep = deploys.get(m.unit_id)
      const wth = withdraws.get(m.unit_id)
      if (dep) {
        // Has deploy (possibly with withdraw) → reposition to hex
        payload.push({unit_code: m.unit_id, target: 'hex', target_global_row: dep.target_row!, target_global_col: dep.target_col!})
      } else if (wth) {
        // Withdraw only → reserve
        payload.push({unit_code: m.unit_id, target: 'reserve'})
      }
    }
    try {
      const res = await submitAction(simId, 'move_units', roleId, countryId, {moves: payload})
      setResult(res)
      if (res.success) mapRef.current?.contentWindow?.postMessage({type: 'refresh-units'}, '*')
    } catch (e) { setError(e instanceof Error ? e.message : 'Failed') }
    finally { setSubmitting(false) }
  }

  return (
    <div className="flex gap-3" style={{height:'calc(100vh - 180px)'}}>
      {/* LEFT SIDEBAR */}
      <div className="w-1/4 min-w-[240px] flex flex-col gap-2 overflow-y-auto pr-1">
        <div className="flex items-center justify-between">
          <h2 className="font-heading text-h3 text-text-primary">Deploy & Move</h2>
          <button onClick={onClose} className="font-body text-caption text-text-secondary hover:text-text-primary px-2 py-0.5 rounded border border-border">← Back</button>
        </div>

        {loading ? <p className="font-body text-caption text-text-secondary">Loading...</p>
        : result ? (
          <div className="bg-card border border-border rounded-lg p-3 space-y-3">
            <div className={`p-3 rounded-lg border ${result.success ? 'bg-success/5 border-success/20' : 'bg-danger/5 border-danger/20'}`}>
              <h3 className={`font-body text-body-sm font-bold uppercase ${result.success ? 'text-success' : 'text-danger'}`}>
                {result.success ? 'Moves Applied' : 'Move Failed'}
              </h3>
              <p className="font-body text-caption text-text-secondary mt-1">{String(result.narrative??'')}</p>
            </div>
            <div className="flex gap-2">
              <button onClick={() => { setResult(null); setMoves([]); setHexUnits([]); loadUnits() }}
                className="font-body text-caption px-3 py-1.5 rounded bg-action/10 text-action border border-action/30">Move More</button>
              <button onClick={onSubmitted}
                className="font-body text-caption px-3 py-1.5 rounded border border-border text-text-secondary">← Done</button>
            </div>
          </div>
        ) : (<>
          {/* Mode toggle */}
          <div className="flex gap-1">
            <button onClick={()=>{setMode('withdraw');setSelectedUnit(null)}}
              className={`flex-1 font-body text-caption py-1.5 rounded transition-colors ${
                mode==='withdraw'?'bg-warning/10 text-warning border border-warning/40 font-medium':'bg-card border border-border text-text-secondary hover:text-text-primary'}`}>
              Withdraw
            </button>
            <button onClick={()=>{setMode('deploy');setHexUnits([])}}
              className={`flex-1 font-body text-caption py-1.5 rounded transition-colors ${
                mode==='deploy'?'bg-action/10 text-action border border-action/40 font-medium':'bg-card border border-border text-text-secondary hover:text-text-primary'}`}>
              Deploy
            </button>
          </div>

          {/* Mode instruction */}
          {mode === 'withdraw' ? (
            <p className="font-body text-caption text-warning/80">Click a hex on the map to withdraw units to reserve.</p>
          ) : selectedUnit ? (
            <div className="bg-action/10 border border-action/30 rounded-lg p-2 flex items-center gap-2">
              <UnitIcon type={selectedUnit.unit_type} size={20} className="text-action"/>
              <span className="font-body text-caption text-action flex-1">Click hex to deploy</span>
              <button onClick={()=>setSelectedUnit(null)} className="text-text-secondary text-sm">✕</button>
            </div>
          ) : (
            <p className="font-body text-caption text-action/80">Select a unit from reserve to deploy.</p>
          )}

          {/* Withdraw: units at clicked hex */}
          {mode === 'withdraw' && hexUnits.length > 0 && (
            <div className="bg-card border border-warning/30 rounded-lg p-3 space-y-1">
              <span className="font-body text-caption text-text-secondary">Units at hex:</span>
              <div className="flex flex-wrap gap-1">
                {hexUnits.map(u =>
                  <button key={u.unit_id} title={u.unit_id} onClick={()=>withdrawUnit(u)}
                    className="inline-flex items-center justify-center w-10 h-10 rounded border-2 border-warning/40 text-text-secondary hover:bg-warning/10 hover:text-warning transition-colors">
                    <UnitIcon type={u.unit_type} size={22}/>
                  </button>
                )}
              </div>
            </div>
          )}

          {/* Reserve pool */}
          {Object.keys(reserveByType).length > 0 && (
            <div className="bg-card border border-border rounded-lg p-3 space-y-2">
              <h3 className="font-body text-caption text-text-secondary uppercase tracking-wider">Reserve ({effectiveReserve.length})</h3>
              {Object.entries(reserveByType).map(([type, units]) => (
                <div key={type} className="space-y-1">
                  <span className="font-body text-caption text-text-secondary">{UNIT_TYPE_LABELS[type]??type}</span>
                  <div className="flex flex-wrap gap-1">
                    {units.filter(u => !moves.some(m => m.unit_id === u.unit_id)).map(u => {
                      const isSelected = selectedUnit?.unit_id === u.unit_id
                      return <button key={u.unit_id} title={u.unit_id}
                        onClick={()=>{setSelectedUnit({unit_id:u.unit_id,unit_type:u.unit_type});setMode('deploy');setError(null)}}
                        className={`inline-flex items-center justify-center w-9 h-9 rounded border-2 transition-colors ${
                          isSelected?'bg-action/10 border-action text-action':
                          'border-border text-text-secondary hover:border-action/30 hover:text-action'}`}>
                        <UnitIcon type={type} size={20}/>
                      </button>
                    })}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Queued changes */}
          <div className="bg-card border border-border rounded-lg p-3 space-y-2">
            <h3 className="font-body text-caption text-text-secondary uppercase tracking-wider">Changes ({moves.length})</h3>
            {moves.length > 0 && (<>
              <button onClick={handleSubmit} disabled={submitting}
                className="w-full font-body text-caption font-bold uppercase py-2 rounded bg-action text-white hover:bg-action/80 disabled:opacity-50">
                {submitting ? 'Submitting...' : `Submit ${moves.length} Change(s)`}
              </button>
              <button onClick={discardAll}
                className="w-full font-body text-caption py-1 rounded border border-danger/30 text-danger/70 hover:bg-danger/5 hover:text-danger transition-colors">
                Discard All
              </button>
            </>)}
            {moves.length === 0
              ? <p className="font-body text-caption text-text-secondary/50">No changes queued yet.</p>
              : <div className="space-y-1">
                {moves.map((m, idx) => (
                  <div key={`${m.unit_id}_${m.action}_${idx}`} className="flex items-center justify-between gap-1 py-1 border-b border-border/30 last:border-0">
                    <div className="flex items-center gap-1.5 min-w-0">
                      <UnitIcon type={m.unit_type} size={16} className="text-text-secondary"/>
                      <span className="font-body text-caption text-text-primary truncate">
                        {m.action==='withdraw'?'→ reserve': m.theater ? `→ theater (${m.theater_row},${m.theater_col})` : `→ (${m.target_row},${m.target_col})`}
                      </span>
                    </div>
                    <button onClick={()=>removeMove(m.unit_id)} className="text-danger/60 hover:text-danger text-sm px-1">✕</button>
                  </div>
                ))}
              </div>}
          </div>
        </>)}

        {error && !result && (
          <div className="bg-danger/5 border border-danger/20 rounded-lg p-2">
            <p className="font-body text-caption text-danger">{error}</p>
          </div>
        )}
      </div>

      {/* RIGHT — Map */}
      <div className="flex-1 flex flex-col gap-1">
        <div className="flex gap-1">
          {(['global','eastern_ereb','mashriq'] as const).map(v=>(
            <button key={v} onClick={()=>mapRef.current?.contentWindow?.postMessage({type:'navigate-theater',theater:v==='global'?'global':v},'*')}
              className="font-body text-caption px-2 py-0.5 rounded border border-border text-text-secondary hover:border-action/30 hover:text-action transition-colors">
              {v==='global'?'Global':v==='eastern_ereb'?'E. Ereb':'Mashriq'}
            </button>
          ))}
        </div>
        <div className="relative flex-1 rounded-lg overflow-hidden border border-border">
          <iframe ref={mapRef}
            src={`/map/deployments.html?display=clean&mode=move&country=${countryId}&sim_run_id=${simId}`}
            className="absolute inset-0 w-full h-full border-0" title="Move Units Map"/>
        </div>
      </div>
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

export function ProposeAgreementForm({roleId,countryId,simId,onClose,onSubmitted}:{
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

export function ProposeTransactionForm({roleId,countryId,simId,onClose,onSubmitted}:{
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
    let cancelled = false
    const load = async (attempt = 1): Promise<void> => {
      const [countriesRes, reservesRes, myCountryRes] = await Promise.all([
        supabase.from('countries').select('id,sim_name,color_ui').eq('sim_run_id',simId).order('sim_name'),
        supabase.from('deployments').select('unit_id,unit_type').eq('sim_run_id',simId).eq('country_code',countryId).eq('unit_status','reserve'),
        supabase.from('countries').select('*').eq('sim_run_id',simId).eq('id',countryId).limit(1),
      ])
      if (cancelled) return
      const gotData = countriesRes.data && countriesRes.data.length > 0
      if (!gotData && attempt < 3) {
        // Data empty or error — retry after brief delay (auth/connection recovery)
        await new Promise(r=>setTimeout(r, 800 * attempt))
        return load(attempt+1)
      }
      setCountries((countriesRes.data??[]).filter((c:{id:string})=>c.id!==countryId) as typeof countries)
      setMyReserves((reservesRes.data??[]) as typeof myReserves)
      if (myCountryRes.data?.[0]) setMyCountry(myCountryRes.data[0])
    }
    load()
    return ()=>{ cancelled=true }
  },[simId,countryId])

  const [outgoing, setOutgoing] = useState<{id:string;counterpart:string;status:string}[]>([])

  useEffect(()=>{
    let cancelled = false
    const load = async () => {
      const { data } = await supabase.from('exchange_transactions').select('id,counterpart,status')
        .eq('sim_run_id',simId).eq('proposer',countryId).in('status',['pending','countered'])
      if (!cancelled) setOutgoing((data??[]) as typeof outgoing)
    }
    load()
    return ()=>{ cancelled=true }
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

export function CartelProductionForm({roleId,countryId,simId,onClose,onSubmitted}:{
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

export function TariffSanctionForm({type,roleId,countryId,simId,onClose,onSubmitted}:{
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
    supabase.from(table).select('target_country_code,level').eq('sim_run_id',simId).eq('imposer_country_code',countryId)
      .then(({data})=>{
        const items = (data??[]).map((r:{target_country_code:string;level:number})=>({target:r.target_country_code,level:r.level}))
        setExisting(items)
        const ch: Record<string,number> = {}
        items.forEach(i=>{ch[i.target]=i.level})
        setChanges(ch)
      })
    // Load received against us
    supabase.from(table).select('imposer_country_code,level').eq('sim_run_id',simId).eq('target_country_code',countryId)
      .then(({data})=>setReceived((data??[]).map((r:{imposer_country_code:string;level:number})=>({imposer:r.imposer_country_code,level:r.level}))))
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

export function BudgetForm({roleId,countryId,simId,onClose,onSubmitted}:{
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
