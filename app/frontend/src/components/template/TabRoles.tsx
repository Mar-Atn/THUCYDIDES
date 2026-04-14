/**
 * TabRoles — Template Editor tab for viewing and editing all participant roles.
 * Loads from the reference sim_run, groups by country, displays in accordion.
 */

import { useState, useEffect, useCallback, useMemo } from 'react'
import {
  getTemplateRoles,
  getTemplateCountries,
  updateRole,
  createRole,
  deleteRole,
  type Role,
  type Country,
} from '@/lib/queries'

/* -------------------------------------------------------------------------- */
/*  Constants                                                                  */
/* -------------------------------------------------------------------------- */

/** Canonical display order: large teams, EU, mid-size, solo alphabetical. */
const COUNTRY_ORDER: string[] = [
  'columbia', 'cathay',
  'gallia', 'teutonia', 'ponte', 'freeland', 'albion',
  'sarmatia', 'ruthenia', 'persia',
  'bharata', 'caribe', 'choson', 'formosa', 'hanguk',
  'levantia', 'mirage', 'phrygia', 'solaria', 'yamato',
]

const GENDER_OPTIONS = ['M', 'F'] as const

/* -------------------------------------------------------------------------- */
/*  Helpers                                                                    */
/* -------------------------------------------------------------------------- */

function capitalize(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1)
}

/** Sort country IDs according to COUNTRY_ORDER. */
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

/** Convert comma-separated string to array, filtering empties. */
function csvToArray(s: string): string[] {
  return s.split(',').map((v) => v.trim()).filter(Boolean)
}

/** Convert array to comma-separated string. */
function arrayToCsv(arr: string[]): string {
  return arr.join(', ')
}

/* -------------------------------------------------------------------------- */
/*  Field components                                                           */
/* -------------------------------------------------------------------------- */

interface NumberFieldProps {
  label: string
  value: number
  onChange: (v: number) => void
  step?: number
  min?: number
  max?: number
}

function NumberField({ label, value, onChange, step, min, max }: NumberFieldProps) {
  return (
    <div className="flex flex-col gap-1">
      <label className="font-body text-caption text-text-secondary">{label}</label>
      <input
        type="number"
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value) || 0)}
        step={step}
        min={min}
        max={max}
        className="font-data text-data bg-base border border-border rounded px-2 py-1.5 text-text-primary focus:border-action focus:outline-none"
      />
    </div>
  )
}

interface TextFieldProps {
  label: string
  value: string
  onChange: (v: string) => void
}

function TextField({ label, value, onChange }: TextFieldProps) {
  return (
    <div className="flex flex-col gap-1">
      <label className="font-body text-caption text-text-secondary">{label}</label>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="font-body text-body-sm bg-base border border-border rounded px-2 py-1.5 text-text-primary focus:border-action focus:outline-none"
      />
    </div>
  )
}

interface TextAreaFieldProps {
  label: string
  value: string
  onChange: (v: string) => void
  rows?: number
}

function TextAreaField({ label, value, onChange, rows = 3 }: TextAreaFieldProps) {
  return (
    <div className="flex flex-col gap-1">
      <label className="font-body text-caption text-text-secondary">{label}</label>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        rows={rows}
        className="font-body text-body-sm bg-base border border-border rounded px-2 py-1.5 text-text-primary focus:border-action focus:outline-none resize-y"
      />
    </div>
  )
}

interface SelectFieldProps {
  label: string
  value: string
  options: readonly string[]
  onChange: (v: string) => void
}

function SelectField({ label, value, options, onChange }: SelectFieldProps) {
  return (
    <div className="flex flex-col gap-1">
      <label className="font-body text-caption text-text-secondary">{label}</label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="font-body text-body-sm bg-base border border-border rounded px-2 py-1.5 text-text-primary focus:border-action focus:outline-none"
      >
        {options.map((opt) => (
          <option key={opt} value={opt}>{opt}</option>
        ))}
      </select>
    </div>
  )
}

interface CheckboxFieldProps {
  label: string
  checked: boolean
  onChange: (v: boolean) => void
}

function CheckboxField({ label, checked, onChange }: CheckboxFieldProps) {
  return (
    <label className="flex items-center gap-2 cursor-pointer">
      <input
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        className="w-4 h-4 rounded border-border text-action focus:ring-action"
      />
      <span className="font-body text-body-sm text-text-primary">{label}</span>
    </label>
  )
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
/*  Role badges                                                                */
/* -------------------------------------------------------------------------- */

function RoleBadges({ role }: { role: Role }) {
  return (
    <>
      {role.is_head_of_state && (
        <span className="font-body text-caption font-medium bg-warning/10 text-warning px-1.5 py-0.5 rounded ml-2">
          HoS
        </span>
      )}
      {role.is_military_chief && !role.is_head_of_state && (
        <span className="font-body text-caption font-medium bg-danger/10 text-danger px-1.5 py-0.5 rounded ml-2">
          Military
        </span>
      )}
      {role.is_economy_officer && !role.is_head_of_state && (
        <span className="font-body text-caption font-medium bg-accent/10 text-accent px-1.5 py-0.5 rounded ml-2">
          Economy
        </span>
      )}
      {role.expansion_role && (
        <span className="font-body text-caption font-medium text-text-secondary bg-border/50 px-1.5 py-0.5 rounded ml-2">
          optional
        </span>
      )}
    </>
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
              <option key={cid} value={cid}>{capitalize(cid)}</option>
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
/*  Role editor (expanded panel)                                               */
/* -------------------------------------------------------------------------- */

interface RoleEditorProps {
  role: Role
  countryIds: string[]
  onSave: (updated: Role) => Promise<void>
  onDelete: (id: string) => Promise<void>
}

function RoleEditor({ role, countryIds, onSave, onDelete }: RoleEditorProps) {
  const [draft, setDraft] = useState<Role>({ ...role })
  const [saving, setSaving] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(false)
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; msg: string } | null>(null)

  /** Reset draft when the role prop changes. */
  useEffect(() => {
    setDraft({ ...role })
  }, [role])

  const set = useCallback(<K extends keyof Role>(key: K, value: Role[K]) => {
    setDraft((prev) => ({ ...prev, [key]: value }))
  }, [])

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

  return (
    <div className="px-4 py-4 space-y-2">
      {/* Identity */}
      <SectionHeader title="Identity" />
      <div className="grid grid-cols-2 gap-4">
        <TextField label="character_name" value={draft.character_name} onChange={(v) => set('character_name', v)} />
        <TextField label="title" value={draft.title} onChange={(v) => set('title', v)} />
        <NumberField label="age" value={draft.age} onChange={(v) => set('age', v)} min={18} max={100} />
        <SelectField label="gender" value={draft.gender} options={GENDER_OPTIONS} onChange={(v) => set('gender', v)} />
        <SelectField label="country_id" value={draft.country_id} options={countryIds} onChange={(v) => set('country_id', v)} />
        <TextField label="team" value={draft.team} onChange={(v) => set('team', v)} />
        <TextField label="faction" value={draft.faction} onChange={(v) => set('faction', v)} />
      </div>
      <div className="mt-2">
        <TextAreaField label="public_bio" value={draft.public_bio} onChange={(v) => set('public_bio', v)} rows={3} />
      </div>

      {/* Position */}
      <SectionHeader title="Position" />
      <div className="grid grid-cols-2 gap-4">
        <CheckboxField label="is_head_of_state" checked={draft.is_head_of_state} onChange={(v) => set('is_head_of_state', v)} />
        <CheckboxField label="is_military_chief" checked={draft.is_military_chief} onChange={(v) => set('is_military_chief', v)} />
        <CheckboxField label="Economy Officer" checked={draft.is_economy_officer} onChange={(v) => set('is_economy_officer', v)} />
        <CheckboxField label="is_diplomat" checked={draft.is_diplomat} onChange={(v) => set('is_diplomat', v)} />
        <NumberField label="parliament_seat" value={draft.parliament_seat} onChange={(v) => set('parliament_seat', v)} min={0} />
      </div>

      {/* Resources */}
      <SectionHeader title="Resources" />
      <div className="grid grid-cols-2 gap-4">
        <NumberField label="personal_coins" value={draft.personal_coins} onChange={(v) => set('personal_coins', v)} step={0.01} min={0} />
      </div>

      {/* Covert Ops Deck */}
      <SectionHeader title="Covert Ops Deck" />
      <div className="grid grid-cols-2 gap-4">
        <NumberField label="intelligence_pool" value={draft.intelligence_pool} onChange={(v) => set('intelligence_pool', v)} min={0} />
        <NumberField label="sabotage_cards" value={draft.sabotage_cards} onChange={(v) => set('sabotage_cards', v)} min={0} />
        <NumberField label="cyber_cards" value={draft.cyber_cards} onChange={(v) => set('cyber_cards', v)} min={0} />
        <NumberField label="disinfo_cards" value={draft.disinfo_cards} onChange={(v) => set('disinfo_cards', v)} min={0} />
        <NumberField label="election_meddling_cards" value={draft.election_meddling_cards} onChange={(v) => set('election_meddling_cards', v)} min={0} />
        <NumberField label="assassination_cards" value={draft.assassination_cards} onChange={(v) => set('assassination_cards', v)} min={0} />
        <NumberField label="protest_stim_cards" value={draft.protest_stim_cards} onChange={(v) => set('protest_stim_cards', v)} min={0} />
        <NumberField label="fatherland_appeal" value={draft.fatherland_appeal} onChange={(v) => set('fatherland_appeal', v)} min={0} />
      </div>

      {/* Role Definition */}
      <SectionHeader title="Role Definition" />
      <div className="space-y-3">
        <TextField
          label="powers (comma-separated)"
          value={arrayToCsv(draft.powers)}
          onChange={(v) => set('powers', csvToArray(v))}
        />
        <TextField
          label="objectives (comma-separated)"
          value={arrayToCsv(draft.objectives)}
          onChange={(v) => set('objectives', csvToArray(v))}
        />
        <TextField label="ticking_clock" value={draft.ticking_clock} onChange={(v) => set('ticking_clock', v)} />
      </div>

      {/* Config */}
      <SectionHeader title="Config" />
      <div className="grid grid-cols-2 gap-4">
        <CheckboxField label="expansion_role" checked={draft.expansion_role} onChange={(v) => set('expansion_role', v)} />
        <CheckboxField label="ai_candidate" checked={draft.ai_candidate} onChange={(v) => set('ai_candidate', v)} />
        <CheckboxField label="is_ai_operated" checked={draft.is_ai_operated} onChange={(v) => set('is_ai_operated', v)} />
        <TextField label="brief_file" value={draft.brief_file} onChange={(v) => set('brief_file', v)} />
      </div>

      {/* Save */}
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

      {/* Delete */}
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
/*  Main tab component                                                         */
/* -------------------------------------------------------------------------- */

interface TabRolesProps {
  templateId: string
}

export function TabRoles({ templateId: _templateId }: TabRolesProps) {
  const [roles, setRoles] = useState<Role[]>([])
  const [countries, setCountries] = useState<Country[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [showAddForm, setShowAddForm] = useState(false)

  const loadData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [rolesData, countriesData] = await Promise.all([
        getTemplateRoles(),
        getTemplateCountries(),
      ])
      setRoles(rolesData)
      setCountries(countriesData)
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to load roles'
      setError(message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadData()
  }, [loadData])

  /** Country IDs for the country dropdown. */
  const countryIds = useMemo(
    () => sortCountryIds(countries.map((c) => c.id)),
    [countries]
  )

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

  const handleSave = useCallback(async (updated: Role) => {
    await updateRole(updated.id, updated)
    setRoles((prev) =>
      prev.map((r) => (r.id === updated.id ? updated : r))
    )
  }, [])

  const handleDelete = useCallback(async (id: string) => {
    await deleteRole(id)
    setRoles((prev) => prev.filter((r) => r.id !== id))
    setExpandedId(null)
  }, [])

  const handleRoleCreated = useCallback(() => {
    setShowAddForm(false)
    loadData()
  }, [loadData])

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
                    {capitalize(countryId)}
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
                          <span className="font-body text-body-sm text-text-primary">
                            {role.character_name}
                          </span>
                          <span className="font-body text-caption text-text-secondary">
                            {role.title}
                          </span>
                          <RoleBadges role={role} />
                        </div>
                        <div className="flex items-center gap-2">
                          {role.is_ai_operated && (
                            <span className="font-body text-caption font-medium bg-accent/10 text-accent px-1.5 py-0.5 rounded">
                              AI
                            </span>
                          )}
                        </div>
                      </button>

                      {/* Expanded editor */}
                      {isExpanded && (
                        <div className="border-t border-border bg-card">
                          <RoleEditor
                            role={role}
                            countryIds={countryIds}
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
