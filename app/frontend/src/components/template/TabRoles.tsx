/**
 * TabRoles — Template Editor tab for viewing and editing all participant roles.
 * Loads from the reference sim_run. Flat list sorted by country order.
 * Expanded view: Identity, Bio & Objectives, Actions (read-only), Org Memberships (read-only), Relationships (read-only).
 */

import { useState, useEffect, useMemo } from 'react'
import {
  getTemplateRoles,
  getTemplateCountries,
  updateRole,
  createRole,
  deleteRole,
  getTemplateRoleActions,
  getTemplateRoleRelationships,
  getTemplateOrgMemberships,
  getTemplateOrganizations,
  type Role,
  type Country,
  type RoleAction,
  type RoleRelationship,
  type OrgMembership,
} from '@/lib/queries'

/* -------------------------------------------------------------------------- */
/*  Constants                                                                  */
/* -------------------------------------------------------------------------- */

const COUNTRY_ORDER: string[] = [
  'columbia', 'cathay',
  'gallia', 'teutonia', 'ponte', 'freeland', 'albion',
  'sarmatia', 'ruthenia', 'persia',
  'bharata', 'caribe', 'choson', 'formosa', 'hanguk',
  'levantia', 'mirage', 'phrygia', 'solaria', 'yamato',
]

const GENDER_OPTIONS = ['M', 'F'] as const
const POSITION_OPTIONS = ['head_of_state', 'military_chief', 'economy_officer', 'diplomat', 'security', 'opposition', 'other'] as const
const PARTY_OPTIONS = ['', 'rep', 'dem', 'independent'] as const

const ACTION_LABELS: Record<string, string> = {
  // HoS only
  reassign_types: 'Re-Assign Role Types', martial_law: 'Martial Law', arrest: 'Arrest',
  // Regular Economic
  set_budget: 'Set Budget', set_tariffs: 'Set Tariffs', set_sanctions: 'Set Sanctions', set_opec: 'Set Cartel Production',
  // Military
  ground_attack: 'Ground Attack', air_strike: 'Air Strike', naval_combat: 'Naval Combat',
  naval_bombardment: 'Naval Bombardment', launch_missile_conventional: 'Launch Missile (conventional)',
  naval_blockade: 'Naval Blockade', move_units: 'Move Units',
  // Nuclear
  nuclear_test: 'Nuclear Test', nuclear_launch_initiate: 'Nuclear Launch (initiate)',
  nuclear_authorize: 'Nuclear Authorization', nuclear_intercept: 'Nuclear Intercept',
  // Transactions & Agreements
  propose_transaction: 'Propose Transaction', accept_transaction: 'Accept/Decline/Counter Transaction',
  propose_agreement: 'Propose Agreement', sign_agreement: 'Sign Agreement', basing_rights: 'Basing Rights',
  // Covert & Intelligence
  intelligence: 'Intelligence', covert_operation: 'Covert Operation', assassination: 'Assassination',
  // Political
  change_leader: 'Change Leader', self_nominate: 'Self-Nominate', cast_vote: 'Cast Vote',
  // Communication
  public_statement: 'Public Statement', call_org_meeting: 'Call Organization Meeting', meet_freely: 'Meet Freely',
}

const ACTION_CATEGORIES: Record<string, string[]> = {
  'HoS Powers': ['reassign_types', 'martial_law', 'arrest'],
  'Regular Economic': ['set_budget', 'set_tariffs', 'set_sanctions', 'set_opec'],
  'Military': ['ground_attack', 'air_strike', 'naval_combat', 'naval_bombardment', 'launch_missile_conventional', 'naval_blockade', 'move_units'],
  'Nuclear': ['nuclear_test', 'nuclear_launch_initiate', 'nuclear_authorize', 'nuclear_intercept'],
  'Transactions & Agreements': ['propose_transaction', 'accept_transaction', 'propose_agreement', 'sign_agreement', 'basing_rights'],
  'Covert & Intelligence': ['intelligence', 'covert_operation', 'assassination'],
  'Political': ['change_leader', 'self_nominate', 'cast_vote'],
  'Communication': ['public_statement', 'call_org_meeting', 'meet_freely'],
}

const POSITION_BADGE: Record<string, { label: string; cls: string }> = {
  head_of_state:  { label: 'HoS',        cls: 'bg-warning/10 text-warning' },
  military_chief: { label: 'Military',    cls: 'bg-danger/10 text-danger' },
  economy_officer:{ label: 'Economy',     cls: 'bg-accent/10 text-accent' },
  diplomat:       { label: 'Diplomat',    cls: 'bg-action/10 text-action' },
  security:       { label: 'Security',    cls: 'bg-text-secondary/10 text-text-primary' },
  opposition:     { label: 'Opposition',  cls: 'bg-danger/20 text-danger' },
  other:          { label: 'Other',       cls: 'bg-base text-text-secondary' },
}

const PARTY_BADGE: Record<string, { label: string; cls: string }> = {
  rep:         { label: 'Rep',         cls: 'bg-danger/10 text-danger' },
  dem:         { label: 'Dem',         cls: 'bg-action/10 text-action' },
  independent: { label: 'Independent', cls: 'bg-base text-text-secondary' },
}

const RELATIONSHIP_COLOR: Record<string, string> = {
  reports_to: 'text-action',
  rival: 'text-warning',
  ally: 'text-success',
  patron: 'text-accent',
  adversary: 'text-danger',
  co_conspirator: 'text-text-primary',
}

/* -------------------------------------------------------------------------- */
/*  Helpers                                                                    */
/* -------------------------------------------------------------------------- */

const cap = (s: string) => s.charAt(0).toUpperCase() + s.slice(1)

function sortCountryIds(ids: string[]): string[] {
  return [...ids].sort((a, b) => {
    const ia = COUNTRY_ORDER.indexOf(a)
    const ib = COUNTRY_ORDER.indexOf(b)
    if (ia >= 0 && ib >= 0) return ia - ib
    if (ia >= 0) return -1
    if (ib >= 0) return 1
    return a.localeCompare(b)
  })
}

function formatLimit(perRound: number | null, total: number | null): string {
  if (perRound !== null && perRound > 0) return `${perRound}/round`
  if (total !== null && total > 0) return `${total}/SIM`
  return 'unlimited'
}

/* -------------------------------------------------------------------------- */
/*  Section header                                                             */
/* -------------------------------------------------------------------------- */

function SectionHeader({ title }: { title: string }) {
  return (
    <h4 className="font-heading text-h3 text-text-primary mt-4 mb-2 border-b border-border pb-1">
      {title}
    </h4>
  )
}

/* -------------------------------------------------------------------------- */
/*  Add Role inline form                                                       */
/* -------------------------------------------------------------------------- */

interface AddRoleFormProps {
  countryIds: string[]
  onCreated: () => void
  onCancel: () => void
}

function AddRoleForm({ countryIds, onCreated, onCancel }: AddRoleFormProps) {
  const [roleId, setRoleId] = useState('')
  const [characterName, setCharacterName] = useState('')
  const [countryId, setCountryId] = useState(countryIds[0] ?? '')
  const [title, setTitle] = useState('')
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleCreate = async () => {
    if (!roleId.trim() || !characterName.trim() || !countryId) {
      setError('Role ID, character name, and country are required.')
      return
    }
    setCreating(true)
    setError(null)
    try {
      await createRole({
        id: roleId.trim().toLowerCase(),
        character_name: characterName.trim(),
        country_id: countryId,
        title: title.trim(),
        status: 'active',
      })
      onCreated()
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to create role'
      setError(message)
    } finally {
      setCreating(false)
    }
  }

  return (
    <div className="border border-border rounded-lg p-4 mb-4 bg-card space-y-3">
      <h3 className="font-heading text-h3 text-text-primary">New Role</h3>
      <div className="grid grid-cols-2 gap-3">
        <div className="flex flex-col gap-1">
          <label className="font-body text-caption text-text-secondary">Role ID (lowercase)</label>
          <input
            type="text"
            value={roleId}
            onChange={(e) => setRoleId(e.target.value.toLowerCase())}
            placeholder="e.g. columbia_finance_minister"
            className="font-body text-body-sm bg-base border border-border rounded px-2 py-1.5 text-text-primary focus:border-action focus:outline-none"
          />
        </div>
        <div className="flex flex-col gap-1">
          <label className="font-body text-caption text-text-secondary">Character Name</label>
          <input
            type="text"
            value={characterName}
            onChange={(e) => setCharacterName(e.target.value)}
            placeholder="e.g. James Carter"
            className="font-body text-body-sm bg-base border border-border rounded px-2 py-1.5 text-text-primary focus:border-action focus:outline-none"
          />
        </div>
        <div className="flex flex-col gap-1">
          <label className="font-body text-caption text-text-secondary">Country</label>
          <select
            value={countryId}
            onChange={(e) => setCountryId(e.target.value)}
            className="font-body text-body-sm bg-base border border-border rounded px-2 py-1.5 text-text-primary focus:border-action focus:outline-none"
          >
            {countryIds.map((cid) => (
              <option key={cid} value={cid}>{cap(cid)}</option>
            ))}
          </select>
        </div>
        <div className="flex flex-col gap-1">
          <label className="font-body text-caption text-text-secondary">Title</label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g. Finance Minister"
            className="font-body text-body-sm bg-base border border-border rounded px-2 py-1.5 text-text-primary focus:border-action focus:outline-none"
          />
        </div>
      </div>
      {error && (
        <p className="font-body text-caption text-danger">{error}</p>
      )}
      <div className="flex items-center gap-2">
        <button
          onClick={handleCreate}
          disabled={creating}
          className="font-body text-body-sm font-medium bg-action text-white px-4 py-2 rounded hover:bg-action/90 transition-colors disabled:opacity-50"
        >
          {creating ? 'Creating...' : 'Create'}
        </button>
        <button
          onClick={onCancel}
          className="font-body text-body-sm text-text-secondary hover:text-text-primary transition-colors px-3 py-2"
        >
          Cancel
        </button>
      </div>
    </div>
  )
}

/* -------------------------------------------------------------------------- */
/*  Actions section (read-only)                                                */
/* -------------------------------------------------------------------------- */

function ActionsSection({ actions }: { actions: RoleAction[] }) {
  const actionSet = useMemo(() => new Set(actions.map((a) => a.action_id)), [actions])
  const actionMap = useMemo(() => {
    const m: Record<string, RoleAction> = {}
    for (const a of actions) m[a.action_id] = a
    return m
  }, [actions])

  const hasAny = actions.length > 0

  if (!hasAny) {
    return (
      <div>
        <SectionHeader title="Actions Available" />
        <p className="font-body text-body-sm text-text-secondary">No actions assigned to this role.</p>
      </div>
    )
  }

  return (
    <div>
      <SectionHeader title="Actions Available" />
      <div className="space-y-3">
        {Object.entries(ACTION_CATEGORIES).map(([category, actionIds]) => {
          const available = actionIds.filter((id) => actionSet.has(id))
          if (available.length === 0) return null
          return (
            <div key={category}>
              <h5 className="font-body text-caption font-medium text-text-secondary mb-1">{category}</h5>
              <table className="w-full text-left">
                <thead>
                  <tr className="border-b border-border">
                    <th className="font-body text-caption text-text-secondary py-1 pr-4">Action</th>
                    <th className="font-body text-caption text-text-secondary py-1">Limit</th>
                  </tr>
                </thead>
                <tbody>
                  {available.map((actionId) => {
                    const ra = actionMap[actionId]
                    return (
                      <tr key={actionId} className="border-b border-border/50">
                        <td className="font-body text-body-sm text-text-primary py-1 pr-4">
                          {ACTION_LABELS[actionId] ?? actionId}
                        </td>
                        <td className="font-data text-data text-text-secondary py-1">
                          {formatLimit(ra?.uses_per_round ?? null, ra?.uses_total ?? null)}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )
        })}
      </div>
    </div>
  )
}

/* -------------------------------------------------------------------------- */
/*  Org memberships section (read-only)                                        */
/* -------------------------------------------------------------------------- */

function OrgMembershipsSection({ memberships, orgNames }: { memberships: OrgMembership[]; orgNames: Record<string, string> }) {
  if (memberships.length === 0) {
    return (
      <div>
        <SectionHeader title="Organization Memberships" />
        <p className="font-body text-body-sm text-text-secondary">No organization memberships.</p>
      </div>
    )
  }

  return (
    <div>
      <SectionHeader title="Organization Memberships" />
      <table className="w-full text-left">
        <thead>
          <tr className="border-b border-border">
            <th className="font-body text-caption text-text-secondary py-1 pr-4">Organization</th>
            <th className="font-body text-caption text-text-secondary py-1">Role in Org</th>
          </tr>
        </thead>
        <tbody>
          {memberships.map((m) => (
            <tr key={m.id} className="border-b border-border/50">
              <td className="font-body text-body-sm text-text-primary py-1 pr-4">
                {orgNames[m.org_id] ?? m.org_id}
              </td>
              <td className="font-body text-body-sm text-text-secondary py-1">
                {m.role_in_org}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

/* -------------------------------------------------------------------------- */
/*  Relationships section (read-only)                                          */
/* -------------------------------------------------------------------------- */

function RelationshipsSection({ relationships, roleNames }: { relationships: RoleRelationship[]; roleNames: Record<string, string> }) {
  if (relationships.length === 0) {
    return (
      <div>
        <SectionHeader title="Relationships" />
        <p className="font-body text-body-sm text-text-secondary">No relationships defined.</p>
      </div>
    )
  }

  return (
    <div>
      <SectionHeader title="Relationships" />
      <table className="w-full text-left">
        <thead>
          <tr className="border-b border-border">
            <th className="font-body text-caption text-text-secondary py-1 pr-4">Other Role</th>
            <th className="font-body text-caption text-text-secondary py-1 pr-4">Type</th>
            <th className="font-body text-caption text-text-secondary py-1">Notes</th>
          </tr>
        </thead>
        <tbody>
          {relationships.map((rel) => {
            const colorCls = RELATIONSHIP_COLOR[rel.relationship_type] ?? 'text-text-secondary'
            return (
              <tr key={rel.id} className="border-b border-border/50">
                <td className="font-body text-body-sm text-text-primary py-1 pr-4">
                  {roleNames[rel.role_a_id] && roleNames[rel.role_b_id]
                    ? roleNames[rel.role_b_id]
                    : rel.role_b_id}
                </td>
                <td className="py-1 pr-4">
                  <span className={`font-body text-caption font-medium ${colorCls}`}>
                    {rel.relationship_type}
                  </span>
                </td>
                <td className="font-body text-caption text-text-secondary py-1">
                  {rel.notes}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

/* -------------------------------------------------------------------------- */
/*  Role editor (expanded panel)                                               */
/* -------------------------------------------------------------------------- */

interface RoleEditorProps {
  role: Role
  countryIds: string[]
  actions: RoleAction[]
  memberships: OrgMembership[]
  relationships: RoleRelationship[]
  orgNames: Record<string, string>
  roleNames: Record<string, string>
  onSave: (updated: Role) => Promise<void>
  onDelete: (id: string) => Promise<void>
}

function RoleEditor({ role, countryIds, actions, memberships, relationships, orgNames, roleNames, onSave, onDelete }: RoleEditorProps) {
  const [draft, setDraft] = useState<Role>({ ...role })
  const [saving, setSaving] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(false)
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; msg: string } | null>(null)

  useEffect(() => {
    setDraft({ ...role })
  }, [role])

  const set = <K extends keyof Role>(key: K, value: Role[K]) => {
    setDraft((prev) => ({ ...prev, [key]: value }))
  }

  const handleSave = async () => {
    setSaving(true)
    setFeedback(null)
    try {
      await onSave(draft)
      setFeedback({ type: 'success', msg: 'Saved' })
      setTimeout(() => setFeedback(null), 2000)
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Save failed'
      setFeedback({ type: 'error', msg: message })
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    setDeleting(true)
    try {
      await onDelete(role.id)
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Delete failed'
      setFeedback({ type: 'error', msg: message })
      setDeleting(false)
      setConfirmDelete(false)
    }
  }

  const isColumbia = draft.country_id === 'columbia'

  return (
    <div className="px-4 py-4 space-y-2">
      {/* 1. Identity */}
      <SectionHeader title="Identity" />
      <div className="grid grid-cols-2 gap-4">
        <div className="flex flex-col gap-1">
          <label className="font-body text-caption text-text-secondary">character_name</label>
          <input
            type="text"
            value={draft.character_name}
            onChange={(e) => set('character_name', e.target.value)}
            className="font-body text-body-sm bg-base border border-border rounded px-2 py-1.5 text-text-primary focus:border-action focus:outline-none"
          />
        </div>
        <div className="flex flex-col gap-1">
          <label className="font-body text-caption text-text-secondary">title</label>
          <input
            type="text"
            value={draft.title}
            onChange={(e) => set('title', e.target.value)}
            className="font-body text-body-sm bg-base border border-border rounded px-2 py-1.5 text-text-primary focus:border-action focus:outline-none"
          />
        </div>
        <div className="flex flex-col gap-1">
          <label className="font-body text-caption text-text-secondary">country_id</label>
          <select
            value={draft.country_id}
            onChange={(e) => set('country_id', e.target.value)}
            className="font-body text-body-sm bg-base border border-border rounded px-2 py-1.5 text-text-primary focus:border-action focus:outline-none"
          >
            {countryIds.map((cid) => (
              <option key={cid} value={cid}>{cap(cid)}</option>
            ))}
          </select>
        </div>
        <div className="flex flex-col gap-1">
          <label className="font-body text-caption text-text-secondary">position_type</label>
          <select
            value={draft.position_type}
            onChange={(e) => set('position_type', e.target.value)}
            className="font-body text-body-sm bg-base border border-border rounded px-2 py-1.5 text-text-primary focus:border-action focus:outline-none"
          >
            {POSITION_OPTIONS.map((opt) => (
              <option key={opt} value={opt}>{cap(opt.replace(/_/g, ' '))}</option>
            ))}
          </select>
        </div>
        {isColumbia && (
          <div className="flex flex-col gap-1">
            <label className="font-body text-caption text-text-secondary">party</label>
            <select
              value={draft.party}
              onChange={(e) => set('party', e.target.value)}
              className="font-body text-body-sm bg-base border border-border rounded px-2 py-1.5 text-text-primary focus:border-action focus:outline-none"
            >
              {PARTY_OPTIONS.map((opt) => (
                <option key={opt} value={opt}>{opt ? cap(opt) : '(none)'}</option>
              ))}
            </select>
          </div>
        )}
        <div className="flex flex-col gap-1">
          <label className="font-body text-caption text-text-secondary">age</label>
          <input
            type="number"
            value={draft.age}
            onChange={(e) => set('age', parseInt(e.target.value) || 0)}
            min={18}
            max={100}
            className="font-data text-data bg-base border border-border rounded px-2 py-1.5 text-text-primary focus:border-action focus:outline-none"
          />
        </div>
        <div className="flex flex-col gap-1">
          <label className="font-body text-caption text-text-secondary">gender</label>
          <select
            value={draft.gender}
            onChange={(e) => set('gender', e.target.value)}
            className="font-body text-body-sm bg-base border border-border rounded px-2 py-1.5 text-text-primary focus:border-action focus:outline-none"
          >
            {GENDER_OPTIONS.map((opt) => (
              <option key={opt} value={opt}>{opt}</option>
            ))}
          </select>
        </div>
      </div>
      <div className="grid grid-cols-2 gap-4 mt-3">
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={draft.expansion_role}
            onChange={(e) => set('expansion_role', e.target.checked)}
            className="w-4 h-4 rounded border-border text-action focus:ring-action"
          />
          <span className="font-body text-body-sm text-text-primary">expansion_role</span>
        </label>
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={draft.ai_candidate}
            onChange={(e) => set('ai_candidate', e.target.checked)}
            className="w-4 h-4 rounded border-border text-action focus:ring-action"
          />
          <span className="font-body text-body-sm text-text-primary">ai_candidate</span>
        </label>
      </div>

      {/* 2. Bio & Objectives */}
      <SectionHeader title="Bio & Objectives" />
      <div className="space-y-3">
        <div className="flex flex-col gap-1">
          <label className="font-body text-caption text-text-secondary">public_bio</label>
          <textarea
            value={draft.public_bio}
            onChange={(e) => set('public_bio', e.target.value)}
            rows={3}
            className="font-body text-body-sm bg-base border border-border rounded px-2 py-1.5 text-text-primary focus:border-action focus:outline-none resize-y"
          />
        </div>
        <div className="flex flex-col gap-1">
          <label className="font-body text-caption text-text-secondary">confidential_brief</label>
          <textarea
            value={draft.confidential_brief}
            onChange={(e) => set('confidential_brief', e.target.value)}
            rows={5}
            className="font-body text-body-sm bg-base border border-border rounded px-2 py-1.5 text-text-primary focus:border-action focus:outline-none resize-y"
          />
        </div>
        <div className="flex flex-col gap-1">
          <label className="font-body text-caption text-text-secondary">objectives (one per line)</label>
          <textarea
            value={Array.isArray(draft.objectives) ? draft.objectives.join('\n') : ''}
            onChange={(e) => set('objectives', e.target.value.split('\n').filter((l) => l.trim() !== ''))}
            rows={3}
            className="font-body text-body-sm bg-base border border-border rounded px-2 py-1.5 text-text-primary focus:border-action focus:outline-none resize-y"
          />
        </div>
      </div>

      {/* 3. Actions Available (read-only) */}
      <ActionsSection actions={actions} />

      {/* 4. Organization Memberships (read-only) */}
      <OrgMembershipsSection memberships={memberships} orgNames={orgNames} />

      {/* 5. Relationships (read-only) */}
      <RelationshipsSection relationships={relationships} roleNames={roleNames} />

      {/* Save button */}
      <div className="flex items-center gap-3 mt-4 pt-3 border-t border-border">
        <button
          onClick={handleSave}
          disabled={saving}
          className="font-body text-body-sm font-medium bg-action text-white px-4 py-2 rounded hover:bg-action/90 transition-colors disabled:opacity-50"
        >
          {saving ? 'Saving...' : 'Save Role'}
        </button>
        {feedback && (
          <span className={`font-body text-caption ${feedback.type === 'success' ? 'text-success' : 'text-danger'}`}>
            {feedback.msg}
          </span>
        )}
      </div>

      {/* Delete button */}
      <div className="mt-4 pt-3 border-t border-border">
        {!confirmDelete ? (
          <button
            onClick={() => setConfirmDelete(true)}
            className="font-body text-body-sm font-medium text-danger hover:text-danger/80 transition-colors px-3 py-1.5 border border-danger/30 rounded hover:bg-danger/5"
          >
            Delete Role
          </button>
        ) : (
          <div className="flex items-center gap-3">
            <span className="font-body text-body-sm text-danger">
              Delete &ldquo;{role.character_name}&rdquo;? This cannot be undone.
            </span>
            <button
              onClick={handleDelete}
              disabled={deleting}
              className="font-body text-body-sm font-medium bg-danger text-white px-4 py-1.5 rounded hover:bg-danger/90 transition-colors disabled:opacity-50"
            >
              {deleting ? 'Deleting...' : 'Confirm Delete'}
            </button>
            <button
              onClick={() => setConfirmDelete(false)}
              className="font-body text-body-sm text-text-secondary hover:text-text-primary transition-colors"
            >
              Cancel
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

/* -------------------------------------------------------------------------- */
/*  Collapsed role row badges                                                  */
/* -------------------------------------------------------------------------- */

function CollapsedBadges({ role }: { role: Role }) {
  const pos = POSITION_BADGE[role.position_type]
  const party = role.country_id === 'columbia' && role.party ? PARTY_BADGE[role.party] : null

  return (
    <>
      {pos && (
        <span className={`font-body text-caption font-medium px-1.5 py-0.5 rounded ml-2 ${pos.cls}`}>
          {pos.label}
        </span>
      )}
      {party && (
        <span className={`font-body text-caption font-medium px-1.5 py-0.5 rounded ml-1 ${party.cls}`}>
          {party.label}
        </span>
      )}
      {role.expansion_role && (
        <span className="font-body text-caption font-medium text-text-secondary bg-border/50 px-1.5 py-0.5 rounded ml-1">
          optional
        </span>
      )}
    </>
  )
}

/* -------------------------------------------------------------------------- */
/*  Main tab component                                                         */
/* -------------------------------------------------------------------------- */

interface TabRolesProps {
  templateId: string
}

export function TabRoles({ templateId: _templateId }: TabRolesProps) {
  const [roles, setRoles] = useState<Role[]>([])
  const [countries, setCountries] = useState<Country[]>([])
  const [allActions, setAllActions] = useState<RoleAction[]>([])
  const [allMemberships, setAllMemberships] = useState<OrgMembership[]>([])
  const [allRelationships, setAllRelationships] = useState<RoleRelationship[]>([])
  const [orgNames, setOrgNames] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [showAddForm, setShowAddForm] = useState(false)

  const loadData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [rolesData, countriesData, actionsData, membershipsData, relationshipsData, orgsData] = await Promise.all([
        getTemplateRoles(),
        getTemplateCountries(),
        getTemplateRoleActions(),
        getTemplateOrgMemberships(),
        getTemplateRoleRelationships(),
        getTemplateOrganizations(),
      ])
      setRoles(rolesData)
      setCountries(countriesData)
      setAllActions(actionsData)
      setAllMemberships(membershipsData)
      setAllRelationships(relationshipsData)
      const names: Record<string, string> = {}
      for (const org of orgsData) names[org.id] = org.sim_name
      setOrgNames(names)
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to load roles'
      setError(message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  /** Country IDs for dropdowns. */
  const countryIds = useMemo(
    () => sortCountryIds(countries.map((c) => c.id)),
    [countries]
  )

  /** Role name lookup. */
  const roleNames = useMemo(() => {
    const m: Record<string, string> = {}
    for (const r of roles) m[r.id] = `${r.character_name} (${cap(r.country_id)})`
    return m
  }, [roles])

  /** Actions indexed by role_id. */
  const actionsByRole = useMemo(() => {
    const m: Record<string, RoleAction[]> = {}
    for (const a of allActions) {
      if (!m[a.role_id]) m[a.role_id] = []
      m[a.role_id].push(a)
    }
    return m
  }, [allActions])

  /** Memberships indexed by role_id. */
  const membershipsByRole = useMemo(() => {
    const m: Record<string, OrgMembership[]> = {}
    for (const mb of allMemberships) {
      if (mb.role_id) {
        if (!m[mb.role_id]) m[mb.role_id] = []
        m[mb.role_id].push(mb)
      }
    }
    return m
  }, [allMemberships])

  /** Relationships indexed by role_id (both sides). */
  const relationshipsByRole = useMemo(() => {
    const m: Record<string, RoleRelationship[]> = {}
    for (const rel of allRelationships) {
      // Index under role_a — show role_b as the "other"
      if (!m[rel.role_a_id]) m[rel.role_a_id] = []
      m[rel.role_a_id].push(rel)
      // Also index under role_b with swapped display
      if (rel.role_b_id !== rel.role_a_id) {
        if (!m[rel.role_b_id]) m[rel.role_b_id] = []
        m[rel.role_b_id].push({ ...rel, role_a_id: rel.role_b_id, role_b_id: rel.role_a_id })
      }
    }
    return m
  }, [allRelationships])

  /** Group roles by country_id. */
  const rolesByCountry = useMemo(() => {
    const map: Record<string, Role[]> = {}
    for (const role of roles) {
      const key = role.country_id
      if (!map[key]) map[key] = []
      map[key].push(role)
    }
    return map
  }, [roles])

  /** Sorted country IDs that have roles. */
  const sortedCountryIds = useMemo(
    () => sortCountryIds(Object.keys(rolesByCountry)),
    [rolesByCountry]
  )

  const handleSave = async (updated: Role) => {
    await updateRole(updated.id, updated)
    setRoles((prev) =>
      prev.map((r) => (r.id === updated.id ? updated : r))
    )
  }

  const handleDelete = async (id: string) => {
    await deleteRole(id)
    setRoles((prev) => prev.filter((r) => r.id !== id))
    setExpandedId(null)
  }

  const handleRoleCreated = () => {
    setShowAddForm(false)
    loadData()
  }

  if (loading) {
    return (
      <div className="p-6">
        <p className="font-body text-body-sm text-text-secondary">Loading roles...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6">
        <p className="font-body text-body-sm text-danger">{error}</p>
        <button
          onClick={loadData}
          className="font-body text-body-sm text-action mt-2 hover:underline"
        >
          Retry
        </button>
      </div>
    )
  }

  return (
    <div>
      <div className="flex items-center gap-4 mb-2">
        <h2 className="font-heading text-h2 text-text-primary">Roles</h2>
        <button
          onClick={() => setShowAddForm((prev) => !prev)}
          className="font-body text-body-sm font-medium bg-action text-white px-3 py-1.5 rounded hover:bg-action/90 transition-colors"
        >
          {showAddForm ? 'Cancel' : 'Add Role'}
        </button>
      </div>
      <p className="font-body text-body-sm text-text-secondary mb-6">
        Edit participant roles. {roles.length} roles across {sortedCountryIds.length} countries.
      </p>

      {showAddForm && (
        <AddRoleForm
          countryIds={countryIds}
          onCreated={handleRoleCreated}
          onCancel={() => setShowAddForm(false)}
        />
      )}

      <div className="space-y-4">
        {sortedCountryIds.map((countryId) => {
          const countryRoles = rolesByCountry[countryId] ?? []

          return (
            <div
              key={countryId}
              className="border border-border rounded-lg overflow-hidden"
            >
              {/* Country group header */}
              <div className="bg-base px-4 py-3 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <h3 className="font-heading text-h3 text-text-primary">
                    {cap(countryId)}
                  </h3>
                  <span className="font-data text-data text-text-secondary">
                    {countryRoles.length} roles
                  </span>
                </div>
              </div>

              {/* Role rows */}
              <div className="divide-y divide-border">
                {countryRoles.map((role) => {
                  const isExpanded = expandedId === role.id
                  return (
                    <div key={role.id}>
                      {/* Collapsed role row */}
                      <button
                        onClick={() => setExpandedId(isExpanded ? null : role.id)}
                        className="w-full px-4 py-2.5 flex items-center justify-between hover:bg-card/30 transition-colors"
                      >
                        <div className="flex items-center gap-3">
                          <span
                            className={`transition-transform text-text-secondary text-xs ${isExpanded ? 'rotate-90' : ''}`}
                          >
                            {'\u25B6'}
                          </span>
                          <span className="font-body text-body-sm text-text-primary font-medium">
                            {role.character_name}
                          </span>
                          <span className="font-body text-caption text-text-secondary">
                            {role.title}
                          </span>
                          <span className="font-body text-caption text-text-secondary">
                            {cap(role.country_id)}
                          </span>
                          <CollapsedBadges role={role} />
                        </div>
                      </button>

                      {/* Expanded editor */}
                      {isExpanded && (
                        <div className="border-t border-border bg-card">
                          <RoleEditor
                            role={role}
                            countryIds={countryIds}
                            actions={actionsByRole[role.id] ?? []}
                            memberships={membershipsByRole[role.id] ?? []}
                            relationships={relationshipsByRole[role.id] ?? []}
                            orgNames={orgNames}
                            roleNames={roleNames}
                            onSave={handleSave}
                            onDelete={handleDelete}
                          />
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
