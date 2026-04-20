/**
 * TabActions — Template Editor tab for viewing action permissions across all roles.
 * Read-only action library with detail view showing which roles have each action.
 * Loads roles and role_actions from the reference sim_run.
 */

import { useState, useEffect, useMemo, useCallback } from 'react'
import {
  getTemplateRoles,
  getTemplateRoleActions,
  getTemplateCountries,
  simAction,
  type Role,
  type RoleAction,
  type Country,
} from '@/lib/queries'
import {
  ACTION_LABELS,
  ACTION_CATEGORIES,
  REACTIVE_ACTIONS,
  POSITION_LABELS,
  ACTION_POSITIONS,
  ACTION_CONDITIONS,
} from '@/lib/action_constants'

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

/** Position badge styles (reused from TabRoles pattern) */
const POSITION_BADGE: Record<string, { label: string; cls: string }> = {
  head_of_state:  { label: 'HoS',       cls: 'bg-warning/10 text-warning' },
  military:       { label: 'Military',   cls: 'bg-danger/10 text-danger' },
  economy:        { label: 'Economy',    cls: 'bg-accent/10 text-accent' },
  diplomat:       { label: 'Diplomat',   cls: 'bg-action/10 text-action' },
  security:       { label: 'Security',   cls: 'bg-text-secondary/10 text-text-primary' },
  opposition:     { label: 'Opposition', cls: 'bg-danger/20 text-danger' },
  all:            { label: 'All',        cls: 'bg-success/10 text-success' },
  org_members:    { label: 'Org Members',cls: 'bg-action/10 text-action' },
  org_chairman:   { label: 'Chairman',   cls: 'bg-warning/10 text-warning' },
}

/* -------------------------------------------------------------------------- */
/*  Helpers                                                                    */
/* -------------------------------------------------------------------------- */

function capitalize(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1)
}

function getActionType(actionId: string): 'Reactive' | 'Dynamic' | 'Static' {
  if (REACTIVE_ACTIONS.has(actionId)) return 'Reactive'
  if (ACTION_CONDITIONS[actionId]) return 'Dynamic'
  return 'Static'
}

function getTypeStyle(type: string): string {
  switch (type) {
    case 'Reactive': return 'text-action'
    case 'Dynamic': return 'text-warning'
    default: return 'text-text-secondary'
  }
}

function sortCountriesById(ids: string[]): string[] {
  return [...ids].sort((a, b) => {
    const ia = COUNTRY_ORDER.indexOf(a)
    const ib = COUNTRY_ORDER.indexOf(b)
    if (ia >= 0 && ib >= 0) return ia - ib
    if (ia >= 0) return -1
    if (ib >= 0) return 1
    return a.localeCompare(b)
  })
}

/* -------------------------------------------------------------------------- */
/*  Position badge component                                                   */
/* -------------------------------------------------------------------------- */

function PositionBadge({ position }: { position: string }) {
  const badge = POSITION_BADGE[position]
  if (badge) {
    return (
      <span className={`inline-block px-1.5 py-0.5 rounded text-[10px] font-medium ${badge.cls}`}>
        {badge.label}
      </span>
    )
  }
  // Fallback for custom labels like "2 per country (priority)"
  return (
    <span className="inline-block px-1.5 py-0.5 rounded text-[10px] font-medium bg-base text-text-secondary">
      {position}
    </span>
  )
}

/* -------------------------------------------------------------------------- */
/*  Action list item (left panel)                                              */
/* -------------------------------------------------------------------------- */

interface ActionListItemProps {
  actionId: string
  isSelected: boolean
  onSelect: () => void
}

function ActionListItem({ actionId, isSelected, onSelect }: ActionListItemProps) {
  const label = ACTION_LABELS[actionId] ?? actionId
  const type = getActionType(actionId)
  const positions = ACTION_POSITIONS[actionId] ?? []

  return (
    <button
      onClick={onSelect}
      className={`w-full text-left px-3 py-2 rounded transition-colors ${
        isSelected
          ? 'bg-action/10 border border-action/30'
          : 'hover:bg-base border border-transparent'
      }`}
    >
      <div className="flex items-center justify-between gap-2">
        <span className="font-body text-body-sm text-text-primary truncate">
          {label}
        </span>
        <span className={`font-body text-caption whitespace-nowrap ${getTypeStyle(type)}`}>
          {type}
        </span>
      </div>
      {positions.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-1">
          {positions.map((pos) => (
            <PositionBadge key={pos} position={pos} />
          ))}
        </div>
      )}
    </button>
  )
}

/* -------------------------------------------------------------------------- */
/*  Action detail panel (right panel)                                          */
/* -------------------------------------------------------------------------- */

interface ActionDetailProps {
  actionId: string
  roles: Role[]
  roleActions: RoleAction[]
  countries: Country[]
}

function ActionDetail({ actionId, roles, roleActions, countries }: ActionDetailProps) {
  const label = ACTION_LABELS[actionId] ?? actionId
  const type = getActionType(actionId)
  const positions = ACTION_POSITIONS[actionId] ?? []
  const condition = ACTION_CONDITIONS[actionId]
  const isReactive = REACTIVE_ACTIONS.has(actionId)

  // Build map: which roles have this action
  const rolesWithAction = useMemo(() => {
    const roleIdSet = new Set(
      roleActions
        .filter((ra) => ra.action_id === actionId)
        .map((ra) => ra.role_id)
    )
    return roleIdSet
  }, [roleActions, actionId])

  // Group roles by country
  const rolesByCountry = useMemo(() => {
    const map = new Map<string, Role[]>()
    for (const role of roles) {
      const list = map.get(role.country_code) ?? []
      list.push(role)
      map.set(role.country_code, list)
    }
    return map
  }, [roles])

  // Country lookup
  const countryMap = useMemo(() => {
    const m = new Map<string, Country>()
    for (const c of countries) m.set(c.id, c)
    return m
  }, [countries])

  const sortedCountryIds = useMemo(
    () => sortCountriesById(Array.from(rolesByCountry.keys())),
    [rolesByCountry]
  )

  // Count totals
  const totalAssigned = roles.filter((r) => rolesWithAction.has(r.id)).length

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <h2 className="font-heading text-h2 text-text-primary mb-2">{label}</h2>
        <div className="flex items-center gap-3 mb-3">
          <span className={`font-body text-body-sm font-medium ${getTypeStyle(type)}`}>
            {type}
          </span>
          {type === 'Reactive' && (
            <span className="font-body text-caption text-text-secondary">
              Computed at runtime
            </span>
          )}
        </div>

        {/* Positions */}
        {positions.length > 0 && (
          <div className="mb-3">
            <span className="font-body text-caption text-text-secondary mr-2">
              Positions:
            </span>
            <span className="inline-flex flex-wrap gap-1">
              {positions.map((pos) => (
                <PositionBadge key={pos} position={pos} />
              ))}
            </span>
          </div>
        )}

        {/* Condition */}
        {condition && (
          <div className="mb-3">
            <span className="font-body text-caption text-text-secondary mr-2">
              Condition:
            </span>
            <span className="font-data text-data text-warning">
              {condition}
            </span>
          </div>
        )}

        {/* Summary */}
        <p className="font-body text-caption text-text-secondary">
          {isReactive
            ? 'Reactive actions are not stored in role_actions -- they are computed at runtime when triggering conditions are met.'
            : `Assigned to ${totalAssigned} of ${roles.length} roles across ${sortedCountryIds.length} countries.`
          }
        </p>
      </div>

      {/* Assignment table */}
      <div className="border border-border rounded-lg overflow-hidden">
        <div className="bg-base px-4 py-2 border-b border-border">
          <h3 className="font-heading text-h3 text-text-primary">
            Role Assignments
          </h3>
        </div>
        <div className="max-h-[500px] overflow-y-auto">
          {sortedCountryIds.map((countryId) => {
            const country = countryMap.get(countryId)
            const countryRoles = rolesByCountry.get(countryId) ?? []
            const countryColor = country?.color_ui ?? '#888888'

            return (
              <div key={countryId} className="border-b border-border last:border-b-0">
                {/* Country header */}
                <div className="px-4 py-2 bg-base/50 flex items-center gap-2">
                  <span
                    className="w-3 h-3 rounded-full flex-shrink-0"
                    style={{ backgroundColor: countryColor }}
                  />
                  <span className="font-heading text-caption font-semibold text-text-primary">
                    {capitalize(country?.sim_name ?? countryId)}
                  </span>
                  <span className="font-body text-caption text-text-secondary ml-auto">
                    {countryRoles.filter((r) => rolesWithAction.has(r.id)).length}/{countryRoles.length}
                  </span>
                </div>
                {/* Role rows */}
                {countryRoles.map((role) => {
                  const hasAction = rolesWithAction.has(role.id)
                  const posLabel = POSITION_LABELS[role.position_type] ?? role.position_type

                  return (
                    <div
                      key={role.id}
                      className="px-4 py-1.5 flex items-center gap-3 hover:bg-base/30 transition-colors"
                    >
                      <span className={`w-4 h-4 rounded border flex items-center justify-center flex-shrink-0 ${
                        isReactive
                          ? 'border-text-secondary/30 bg-base'
                          : hasAction
                            ? 'border-success bg-success/10'
                            : 'border-border bg-base'
                      }`}>
                        {!isReactive && hasAction && (
                          <span className="text-success text-xs font-bold">
                            {'\u2713'}
                          </span>
                        )}
                        {isReactive && (
                          <span className="text-text-secondary text-[10px]">--</span>
                        )}
                      </span>
                      <span className="font-body text-body-sm text-text-primary flex-1 truncate">
                        {role.character_name}
                      </span>
                      <span className="font-body text-caption text-text-secondary">
                        {posLabel}
                      </span>
                    </div>
                  )
                })}
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

/* -------------------------------------------------------------------------- */
/*  Main tab component                                                         */
/* -------------------------------------------------------------------------- */

interface TabActionsProps {
  templateId: string
}

export function TabActions({ templateId: _templateId }: TabActionsProps) {
  const [roles, setRoles] = useState<Role[]>([])
  const [roleActions, setRoleActions] = useState<RoleAction[]>([])
  const [countries, setCountries] = useState<Country[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedAction, setSelectedAction] = useState<string | null>(null)
  const [recomputing, setRecomputing] = useState(false)
  const [recomputeResult, setRecomputeResult] = useState<string | null>(null)

  const DEFAULT_SIM_ID = '00000000-0000-0000-0000-000000000001'

  const handleRecompute = async () => {
    if (!confirm('Recompute all action assignments from positions + country state?\n\nManual overrides will be preserved.')) return
    setRecomputing(true)
    setRecomputeResult(null)
    try {
      const res = await simAction(DEFAULT_SIM_ID, 'recompute-actions')
      const added = (res as Record<string, unknown>).total_added ?? 0
      const removed = (res as Record<string, unknown>).total_removed ?? 0
      const preserved = (res as Record<string, unknown>).manual_preserved ?? 0
      setRecomputeResult(`Done: +${added} added, -${removed} removed, ${preserved} manual preserved`)
      loadData()
    } catch (err) {
      setRecomputeResult(`Error: ${err instanceof Error ? err.message : 'Failed'}`)
    } finally { setRecomputing(false) }
  }

  const loadData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [rolesData, actionsData, countriesData] = await Promise.all([
        getTemplateRoles(),
        getTemplateRoleActions(),
        getTemplateCountries(),
      ])
      setRoles(rolesData)
      setRoleActions(actionsData)
      setCountries(countriesData)
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to load action data'
      setError(message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadData()
  }, [loadData])

  // Build flat list of all action IDs from categories
  const allActionIds = useMemo(() => {
    const ids: string[] = []
    for (const actions of Object.values(ACTION_CATEGORIES)) {
      for (const id of actions) {
        ids.push(id)
      }
    }
    return ids
  }, [])

  // Count how many roles have each action (for summary stats)
  const actionRoleCounts = useMemo(() => {
    const counts = new Map<string, number>()
    for (const ra of roleActions) {
      counts.set(ra.action_id, (counts.get(ra.action_id) ?? 0) + 1)
    }
    return counts
  }, [roleActions])

  // Auto-select first action
  useEffect(() => {
    if (!selectedAction && allActionIds.length > 0) {
      setSelectedAction(allActionIds[0])
    }
  }, [selectedAction, allActionIds])

  if (loading) {
    return (
      <div className="p-6">
        <p className="font-body text-body-sm text-text-secondary">
          Loading actions...
        </p>
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
      <div className="flex items-center justify-between mb-1">
        <h2 className="font-heading text-h2 text-text-primary">Actions</h2>
        <button
          onClick={handleRecompute}
          disabled={recomputing}
          className="font-body text-caption font-medium bg-action/10 text-action px-3 py-1.5 rounded hover:bg-action/20 disabled:opacity-50 transition-colors"
        >
          {recomputing ? 'Recomputing...' : 'Recompute from Positions'}
        </button>
      </div>
      <p className="font-body text-body-sm text-text-secondary mb-2">
        Action permissions across all roles. {allActionIds.length} actions defined,{' '}
        {roleActions.length} role-action assignments.
      </p>
      {recomputeResult && (
        <div className={`font-body text-caption px-3 py-2 rounded mb-4 ${
          recomputeResult.startsWith('Error') ? 'bg-danger/5 text-danger' : 'bg-success/5 text-success'
        }`}>
          {recomputeResult}
        </div>
      )}

      <div className="flex gap-6">
        {/* Left panel: action library */}
        <div className="w-[30%] flex-shrink-0">
          <div className="border border-border rounded-lg overflow-hidden">
            <div className="max-h-[600px] overflow-y-auto">
              {Object.entries(ACTION_CATEGORIES).map(([category, actionIds]) => (
                <div key={category}>
                  {/* Category header */}
                  <div className="px-3 py-2 bg-base border-b border-border sticky top-0 z-10">
                    <span className="font-heading text-caption font-semibold text-text-secondary uppercase tracking-wide">
                      {category}
                    </span>
                  </div>
                  {/* Action items */}
                  <div className="p-1">
                    {actionIds.map((actionId) => {
                      const count = actionRoleCounts.get(actionId) ?? 0
                      return (
                        <div key={actionId} className="relative">
                          <ActionListItem
                            actionId={actionId}
                            isSelected={selectedAction === actionId}
                            onSelect={() => setSelectedAction(actionId)}
                          />
                          {count > 0 && !REACTIVE_ACTIONS.has(actionId) && (
                            <span className="absolute top-2 right-2 font-data text-[10px] text-text-secondary">
                              {count}
                            </span>
                          )}
                        </div>
                      )
                    })}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right panel: action detail */}
        <div className="w-[70%]">
          {selectedAction ? (
            <ActionDetail
              actionId={selectedAction}
              roles={roles}
              roleActions={roleActions}
              countries={countries}
            />
          ) : (
            <div className="flex items-center justify-center h-64">
              <p className="font-body text-body-sm text-text-secondary">
                Select an action from the list to view details.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
