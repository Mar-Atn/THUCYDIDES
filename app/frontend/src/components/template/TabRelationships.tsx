/**
 * TabRelationships — bilateral relationship matrix for the template.
 * Displays a country-by-country grid with colored relationship badges.
 * Click a cell to view/edit relationship details in a popup editor.
 */

import { useEffect, useState, useCallback } from 'react'
import {
  getTemplateRelationships,
  getTemplateCountries,
  updateRelationship,
  type Relationship,
  type Country,
} from '@/lib/queries'

/** Capitalize first letter of a country id for display. */
function cap(id: string): string {
  return id.charAt(0).toUpperCase() + id.slice(1)
}

/** Custom country display order: large teams, EU, mid-size, solo alphabetical. */
const COUNTRY_ORDER: string[] = [
  'columbia', 'cathay',
  'gallia', 'teutonia', 'ponte', 'freeland', 'albion',
  'sarmatia', 'ruthenia', 'persia',
  'bharata', 'caribe', 'choson', 'formosa', 'hanguk',
  'levantia', 'mirage', 'phrygia', 'solaria', 'yamato',
]

/** Short labels for relationship types. */
const REL_ABBREV: Record<string, string> = {
  alliance: 'ALI',
  economic_partnership: 'ECO',
  neutral: 'NEU',
  hostile: 'HOS',
  at_war: 'WAR',
}

/** Background color classes for each relationship type. */
const REL_BG: Record<string, string> = {
  alliance: 'bg-green-600 text-white',
  economic_partnership: 'bg-blue-500/70 text-white',
  neutral: 'bg-gray-400/50 text-text-primary',
  hostile: 'bg-orange-500/80 text-white',
  at_war: 'bg-red-900 text-white',
}

/** Relationship type options for the dropdown. */
const RELATIONSHIP_TYPES = [
  'alliance', 'economic_partnership', 'neutral', 'hostile', 'at_war',
] as const

/** Agreement types that can change relations. */
const AGREEMENT_TYPES = [
  'military_alliance', 'trade_agreement', 'peace_treaty', 'ceasefire', 'war_declaration',
] as const

interface CellEditor {
  relationship: Relationship
  saving: boolean
}

interface TabRelationshipsProps {
  templateId: string
}

export function TabRelationships({ templateId: _templateId }: TabRelationshipsProps) {
  const [relationships, setRelationships] = useState<Relationship[]>([])
  const [countries, setCountries] = useState<Country[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [editor, setEditor] = useState<CellEditor | null>(null)

  useEffect(() => {
    const load = async () => {
      try {
        const [relData, countryData] = await Promise.all([
          getTemplateRelationships(),
          getTemplateCountries(),
        ])
        setRelationships(relData)
        setCountries(countryData)
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to load relationships')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  /** Sort countries by COUNTRY_ORDER. */
  const sortedCountryIds = countries
    .map((c) => c.id)
    .sort((a, b) => {
      const ia = COUNTRY_ORDER.indexOf(a)
      const ib = COUNTRY_ORDER.indexOf(b)
      if (ia >= 0 && ib >= 0) return ia - ib
      if (ia >= 0) return -1
      if (ib >= 0) return 1
      return a.localeCompare(b)
    })

  /** Build a lookup map for quick cell access. */
  const relMap = new Map<string, Relationship>()
  for (const r of relationships) {
    relMap.set(`${r.from_country_code}:${r.to_country_code}`, r)
  }

  /** Get a relationship for a cell. */
  function getRelForCell(from: string, to: string): Relationship | undefined {
    return relMap.get(`${from}:${to}`)
  }

  /** Handle cell click — open editor. */
  function handleCellClick(from: string, to: string) {
    if (from === to) return
    const rel = getRelForCell(from, to)
    if (!rel) return
    setEditor({ relationship: { ...rel }, saving: false })
  }

  /** Close editor. */
  function closeEditor() {
    setEditor(null)
  }

  /** Update a field in the editor's local relationship copy. */
  const updateEditorField = useCallback(
    (field: keyof Relationship, value: string | boolean) => {
      setEditor((prev) => {
        if (!prev) return null
        return {
          ...prev,
          relationship: { ...prev.relationship, [field]: value },
        }
      })
    },
    []
  )

  /** Save edited relationship. */
  async function handleSave() {
    if (!editor) return
    setEditor((prev) => (prev ? { ...prev, saving: true } : null))
    try {
      const r = editor.relationship
      await updateRelationship(r.id, {
        relationship: r.relationship,
        status: r.status,
        basing_rights_a_to_b: r.basing_rights_a_to_b,
        basing_rights_b_to_a: r.basing_rights_b_to_a,
      })
      // Update local state
      setRelationships((prev) =>
        prev.map((rel) => (rel.id === r.id ? { ...r } : rel))
      )
      setEditor(null)
    } catch (e) {
      console.error('Failed to save relationship:', e)
      setEditor((prev) => (prev ? { ...prev, saving: false } : null))
    }
  }

  if (loading) {
    return (
      <div>
        <h3 className="font-heading text-h3 text-text-primary mb-2">Relationships</h3>
        <p className="font-body text-body-sm text-text-secondary">Loading...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div>
        <h3 className="font-heading text-h3 text-text-primary mb-2">Relationships</h3>
        <p className="font-body text-body-sm text-danger">{error}</p>
      </div>
    )
  }

  const cellSize = 'min-w-[44px] h-[36px]'

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-heading text-h3 text-text-primary">Relationships</h3>
        <div className="flex items-center gap-4">
          {/* Legend */}
          <div className="flex flex-wrap items-center gap-1">
            {RELATIONSHIP_TYPES.map((type) => (
              <span
                key={type}
                className={`font-data text-[10px] px-1.5 py-0.5 rounded ${REL_BG[type]}`}
              >
                {REL_ABBREV[type]}
              </span>
            ))}
            <span className="font-data text-[10px] px-1.5 py-0.5 rounded bg-warning/20 text-warning font-bold ml-1">
              B = Basing Rights
            </span>
          </div>
        </div>
      </div>

      {/* Matrix container — horizontally scrollable */}
      <div className="overflow-x-auto border border-border rounded-lg">
        <table className="border-collapse">
          <thead>
            <tr>
              {/* Top-left corner cell */}
              <th className="sticky left-0 z-10 bg-card border-b border-r border-border min-w-[80px] px-2 py-1" />
              {/* Column headers — rotated */}
              {sortedCountryIds.map((colId) => (
                <th
                  key={colId}
                  className="border-b border-r border-border px-0 py-1 bg-card"
                >
                  <div
                    className="font-body text-[10px] font-medium text-text-secondary whitespace-nowrap"
                    style={{
                      writingMode: 'vertical-rl',
                      transform: 'rotate(180deg)',
                      height: '72px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'flex-end',
                      paddingBottom: '4px',
                    }}
                  >
                    {cap(colId)}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sortedCountryIds.map((rowId) => (
              <tr key={rowId}>
                {/* Row header — sticky left */}
                <td className="sticky left-0 z-10 bg-card border-b border-r border-border px-2 py-1 font-body text-[11px] font-medium text-text-primary whitespace-nowrap">
                  {cap(rowId)}
                </td>
                {/* Data cells */}
                {sortedCountryIds.map((colId) => {
                  if (rowId === colId) {
                    return (
                      <td
                        key={colId}
                        className={`${cellSize} border-b border-r border-border bg-base/60`}
                      />
                    )
                  }
                  const rel = getRelForCell(rowId, colId)
                  const relType = rel?.relationship ?? 'neutral'
                  const bg = REL_BG[relType] ?? REL_BG.neutral
                  const abbrev = REL_ABBREV[relType] ?? '?'
                  // Basing rights: row country hosts col country's bases
                  const hasBasing = rel?.basing_rights_a_to_b || rel?.basing_rights_b_to_a

                  return (
                    <td
                      key={colId}
                      onClick={() => handleCellClick(rowId, colId)}
                      className={`${cellSize} border-b border-r border-border text-center cursor-pointer hover:opacity-80 transition-opacity relative`}
                    >
                      <span
                        className={`font-data text-[10px] leading-none px-1 py-0.5 rounded ${bg}`}
                      >
                        {abbrev}
                      </span>
                      {hasBasing && (
                        <span
                          className="absolute top-0 right-0.5 text-[9px] leading-none text-warning font-bold"
                          title={`Basing rights: ${rel?.basing_rights_a_to_b ? cap(rowId) + ' hosts ' + cap(colId) : ''}${rel?.basing_rights_a_to_b && rel?.basing_rights_b_to_a ? ' + ' : ''}${rel?.basing_rights_b_to_a ? cap(colId) + ' hosts ' + cap(rowId) : ''}`}
                        >
                          B
                        </span>
                      )}
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Inline editor popup */}
      {editor && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
          <div className="bg-card border border-border rounded-lg shadow-lg p-6 w-[420px] max-h-[90vh] overflow-y-auto">
            <h4 className="font-heading text-h3 text-text-primary mb-4">
              {cap(editor.relationship.from_country_code)} &rarr;{' '}
              {cap(editor.relationship.to_country_code)}
            </h4>

            {/* Dynamic text (read-only context) */}
            {editor.relationship.dynamic && (
              <div className="mb-4">
                <label className="block font-body text-caption text-text-secondary mb-1">
                  Dynamic Context
                </label>
                <p className="font-body text-body-sm text-text-primary bg-base border border-border rounded p-2">
                  {editor.relationship.dynamic}
                </p>
              </div>
            )}

            <div className="space-y-4">
              {/* Relationship type */}
              <div>
                <label className="block font-body text-caption text-text-secondary mb-1">
                  Relationship Type
                </label>
                <select
                  value={editor.relationship.relationship}
                  onChange={(e) => updateEditorField('relationship', e.target.value)}
                  className="w-full bg-base border border-border rounded px-3 py-2 font-body text-body-sm text-text-primary focus:outline-none focus:border-action"
                >
                  {RELATIONSHIP_TYPES.map((t) => (
                    <option key={t} value={t}>
                      {t.replace(/_/g, ' ')}
                    </option>
                  ))}
                </select>
              </div>

              {/* Basing rights */}
              <div className="flex items-center gap-6">
                <label className="flex items-center gap-2 font-body text-body-sm text-text-primary">
                  <input
                    type="checkbox"
                    checked={editor.relationship.basing_rights_a_to_b ?? false}
                    onChange={(e) =>
                      updateEditorField('basing_rights_a_to_b', e.target.checked)
                    }
                  />
                  Basing {cap(editor.relationship.from_country_code)} &rarr;{' '}
                  {cap(editor.relationship.to_country_code)}
                </label>
                <label className="flex items-center gap-2 font-body text-body-sm text-text-primary">
                  <input
                    type="checkbox"
                    checked={editor.relationship.basing_rights_b_to_a ?? false}
                    onChange={(e) =>
                      updateEditorField('basing_rights_b_to_a', e.target.checked)
                    }
                  />
                  Basing {cap(editor.relationship.to_country_code)} &rarr;{' '}
                  {cap(editor.relationship.from_country_code)}
                </label>
              </div>
            </div>

            {/* Buttons */}
            <div className="flex items-center justify-end gap-3 mt-6">
              <button
                onClick={closeEditor}
                className="font-body text-body-sm text-text-secondary hover:text-text-primary px-4 py-2 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={editor.saving}
                className={`font-body text-body-sm font-medium py-2 px-6 rounded transition-opacity ${
                  editor.saving
                    ? 'bg-action/40 text-white/60 cursor-not-allowed'
                    : 'bg-action text-white hover:opacity-90'
                }`}
              >
                {editor.saving ? 'Saving...' : 'Save'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
