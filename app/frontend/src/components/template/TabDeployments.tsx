/**
 * TabDeployments — Unit deployment viewer for the template.
 * Shows all military units grouped by country with zone assignments.
 * Links to the map editor for visual deployment editing.
 */

import { useEffect, useState, useMemo } from 'react'
import { getTemplateDeployments, type Deployment } from '@/lib/queries'

// Served from Vite public/map/ (API proxied to test-interface:8888)
const DEPLOYMENT_EDITOR_URL = '/map/deployments.html'

function cap(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1)
}

const COUNTRY_ORDER = [
  'columbia', 'cathay', 'gallia', 'teutonia', 'ponte', 'freeland', 'albion',
  'sarmatia', 'ruthenia', 'persia', 'bharata', 'caribe', 'choson', 'formosa',
  'hanguk', 'levantia', 'mirage', 'phrygia', 'solaria', 'yamato',
]

const UNIT_LABELS: Record<string, string> = {
  ground: 'Ground',
  naval: 'Naval',
  tactical_air: 'Tactical Air',
  strategic_missile: 'Strategic Missiles',
  air_defense: 'Air Defense',
}

const UNIT_STYLE: Record<string, string> = {
  ground: 'bg-success/10 text-success',
  naval: 'bg-action/10 text-action',
  tactical_air: 'bg-accent/10 text-accent',
  strategic_missile: 'bg-danger/10 text-danger',
  air_defense: 'bg-warning/10 text-warning',
}

interface TabDeploymentsProps {
  templateId: string
}

export function TabDeployments({ templateId: _templateId }: TabDeploymentsProps) {
  const [deployments, setDeployments] = useState<Deployment[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [expandedCountry, setExpandedCountry] = useState<string | null>(null)
  const [showMap, setShowMap] = useState(false)

  useEffect(() => {
    const load = async () => {
      try {
        const data = await getTemplateDeployments()
        setDeployments(data)
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to load deployments')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  // Group by country
  const byCountry = useMemo(() => {
    const grouped: Record<string, Deployment[]> = {}
    for (const d of deployments) {
      if (!grouped[d.country_id]) grouped[d.country_id] = []
      grouped[d.country_id].push(d)
    }
    return grouped
  }, [deployments])

  const sortedCountries = Object.keys(byCountry).sort((a, b) => {
    const ia = COUNTRY_ORDER.indexOf(a)
    const ib = COUNTRY_ORDER.indexOf(b)
    if (ia >= 0 && ib >= 0) return ia - ib
    if (ia >= 0) return -1
    if (ib >= 0) return 1
    return a.localeCompare(b)
  })

  // Global totals
  const totalUnits = deployments.reduce((s, d) => s + d.count, 0)
  const totalByType: Record<string, number> = {}
  for (const d of deployments) {
    totalByType[d.unit_type] = (totalByType[d.unit_type] ?? 0) + d.count
  }

  if (loading) {
    return (
      <div>
        <h3 className="font-heading text-h3 text-text-primary mb-2">Deployments</h3>
        <p className="font-body text-body-sm text-text-secondary">Loading...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div>
        <h3 className="font-heading text-h3 text-text-primary mb-2">Deployments</h3>
        <p className="font-body text-body-sm text-danger">{error}</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-heading text-h3 text-text-primary">Deployments</h3>
          <p className="font-body text-caption text-text-secondary mt-1">
            Initial military unit placement across all countries. Use Edit Deployments for drag-and-drop placement.
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setShowMap(!showMap)}
            className={`font-body text-body-sm font-medium py-2 px-4 rounded transition-opacity ${
              showMap ? 'bg-warning/20 text-warning' : 'bg-action text-white'
            } hover:opacity-90`}
          >
            {showMap ? 'Hide Map' : 'Show Map'}
          </button>
          <a
            href={DEPLOYMENT_EDITOR_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="font-body text-body-sm font-medium py-2 px-4 rounded bg-base border border-border text-text-secondary hover:text-action transition-colors"
          >
            Open in New Tab
          </a>
        </div>
      </div>

      {showMap && (
        <div className="border border-border rounded-lg overflow-hidden bg-card">
          <iframe
            src={DEPLOYMENT_EDITOR_URL}
            title="TTT Deployment Editor"
            className="w-full border-0"
            style={{ height: '70vh', minHeight: '500px' }}
          />
        </div>
      )}

      {/* Global summary */}
      <div className="bg-base border border-border rounded-lg p-4">
        <div className="flex items-center justify-between mb-3">
          <h4 className="font-heading text-h3 text-text-primary">Global Summary</h4>
          <span className="font-data text-data text-text-primary">
            {totalUnits} total units across {sortedCountries.length} countries
          </span>
        </div>
        <div className="flex gap-4">
          {Object.entries(UNIT_LABELS).map(([type, label]) => (
            <div key={type} className="flex items-center gap-2">
              <span className={`font-body text-caption px-1.5 py-0.5 rounded ${UNIT_STYLE[type] ?? 'bg-base text-text-secondary'}`}>
                {label}
              </span>
              <span className="font-data text-data text-text-primary">
                {totalByType[type] ?? 0}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Per-country */}
      <div className="space-y-2">
        {sortedCountries.map((countryId) => {
          const countryDeps = byCountry[countryId]
          const countryTotal = countryDeps.reduce((s, d) => s + d.count, 0)
          const isExpanded = expandedCountry === countryId

          // Unit type breakdown
          const byType: Record<string, number> = {}
          for (const d of countryDeps) {
            byType[d.unit_type] = (byType[d.unit_type] ?? 0) + d.count
          }

          return (
            <div key={countryId} className="border border-border rounded-lg overflow-hidden">
              {/* Country header */}
              <button
                onClick={() => setExpandedCountry(isExpanded ? null : countryId)}
                className="w-full flex items-center justify-between px-4 py-3 bg-card hover:bg-base/50 transition-colors text-left"
              >
                <div className="flex items-center gap-3">
                  <span className="font-heading text-h3 text-text-primary">
                    {cap(countryId)}
                  </span>
                  <span className="font-data text-data text-text-secondary">
                    {countryTotal} units
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  {Object.entries(byType).map(([type, count]) => (
                    <span key={type} className={`font-data text-caption px-1.5 py-0.5 rounded ${UNIT_STYLE[type] ?? ''}`}>
                      {UNIT_LABELS[type]?.slice(0, 3) ?? type}: {count}
                    </span>
                  ))}
                  <span className="font-body text-body text-text-secondary">
                    {isExpanded ? '\u25B2' : '\u25BC'}
                  </span>
                </div>
              </button>

              {/* Expanded: deployment details */}
              {isExpanded && (
                <div className="px-4 py-3 border-t border-border bg-base/30">
                  <table className="w-full border-collapse text-left">
                    <thead>
                      <tr className="border-b border-border">
                        <th className="font-body text-caption text-text-secondary px-3 py-2">Unit Type</th>
                        <th className="font-body text-caption text-text-secondary px-3 py-2 text-right">Count</th>
                        <th className="font-body text-caption text-text-secondary px-3 py-2">Zone</th>
                        <th className="font-body text-caption text-text-secondary px-3 py-2">Notes</th>
                      </tr>
                    </thead>
                    <tbody>
                      {countryDeps.map((d) => (
                        <tr key={d.id} className="border-b border-border/50">
                          <td className="px-3 py-1.5">
                            <span className={`font-body text-caption px-1.5 py-0.5 rounded ${UNIT_STYLE[d.unit_type] ?? ''}`}>
                              {UNIT_LABELS[d.unit_type] ?? d.unit_type}
                            </span>
                          </td>
                          <td className="font-data text-data text-text-secondary px-3 py-1.5 text-center">
                            {d.global_row && d.global_col ? `(${d.global_row},${d.global_col})` : d.unit_status}
                          </td>
                          <td className="font-body text-caption text-text-secondary px-3 py-1.5">
                            {d.notes || '—'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
