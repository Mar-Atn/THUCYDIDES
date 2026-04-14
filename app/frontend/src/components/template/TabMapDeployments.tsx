/**
 * TabMapDeployments — read-only display of zones and unit deployments.
 * Two sections: Zones (grouped by theater) and Deployments (grouped by country).
 */

import { useState, useEffect, useMemo } from 'react'
import {
  getTemplateZones,
  getTemplateDeployments,
  type Zone,
  type Deployment,
} from '@/lib/queries'

/* -------------------------------------------------------------------------- */
/*  Props                                                                      */
/* -------------------------------------------------------------------------- */

interface TabMapDeploymentsProps {
  templateId: string
}

/* -------------------------------------------------------------------------- */
/*  Constants                                                                  */
/* -------------------------------------------------------------------------- */

/** Canonical country display order. */
const COUNTRY_ORDER: string[] = [
  'columbia', 'cathay',
  'gallia', 'teutonia', 'ponte', 'freeland', 'albion',
  'sarmatia', 'ruthenia', 'persia',
  'bharata', 'caribe', 'choson', 'formosa', 'hanguk',
  'levantia', 'mirage', 'phrygia', 'solaria', 'yamato',
]

/** Human-friendly labels for unit types. */
const UNIT_TYPE_LABELS: Record<string, string> = {
  ground: 'Ground',
  naval: 'Naval',
  tactical_air: 'Tactical Air',
  strategic_missile: 'Strategic Missiles',
  air_defense: 'Air Defense',
}

/** Theater display names. */
const THEATER_LABELS: Record<string, string> = {
  global: 'Global',
  eastern_ereb: 'Eastern Ereb',
  mashriq: 'Mashriq',
}

/** Capitalize first letter. */
function cap(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1)
}

/** CSS classes for zone type badges. */
function zoneTypeClasses(type: string): string {
  if (type.startsWith('land')) return 'bg-emerald-500/10 text-emerald-400'
  if (type.startsWith('sea')) return 'bg-blue-500/10 text-blue-400'
  if (type === 'chokepoint') return 'bg-amber-500/10 text-amber-400'
  return 'bg-border text-text-secondary'
}

/** Sort countries by COUNTRY_ORDER, unknowns at end alphabetically. */
function sortCountries(a: string, b: string): number {
  const ia = COUNTRY_ORDER.indexOf(a)
  const ib = COUNTRY_ORDER.indexOf(b)
  if (ia >= 0 && ib >= 0) return ia - ib
  if (ia >= 0) return -1
  if (ib >= 0) return 1
  return a.localeCompare(b)
}

/* -------------------------------------------------------------------------- */
/*  Component                                                                  */
/* -------------------------------------------------------------------------- */

export function TabMapDeployments({ templateId: _templateId }: TabMapDeploymentsProps) {
  const [zones, setZones] = useState<Zone[]>([])
  const [deployments, setDeployments] = useState<Deployment[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  /* ---- Load data ---- */

  useEffect(() => {
    let cancelled = false
    const load = async () => {
      setLoading(true)
      try {
        const [z, d] = await Promise.all([getTemplateZones(), getTemplateDeployments()])
        if (cancelled) return
        setZones(z)
        setDeployments(d)
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : 'Failed to load data')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => { cancelled = true }
  }, [])

  /* ---- Derived: zones grouped by theater ---- */

  const zonesByTheater = useMemo(() => {
    const grouped: Record<string, Zone[]> = {}
    for (const z of zones) {
      const t = z.theater || 'global'
      if (!grouped[t]) grouped[t] = []
      grouped[t].push(z)
    }
    return grouped
  }, [zones])

  const theaterOrder = useMemo(() => {
    const known = ['global', 'eastern_ereb', 'mashriq']
    const extras = Object.keys(zonesByTheater).filter((t) => !known.includes(t)).sort()
    return [...known.filter((t) => zonesByTheater[t]), ...extras]
  }, [zonesByTheater])

  /* ---- Derived: deployments grouped by country ---- */

  const deploymentsByCountry = useMemo(() => {
    const grouped: Record<string, Deployment[]> = {}
    for (const d of deployments) {
      if (!grouped[d.country_id]) grouped[d.country_id] = []
      grouped[d.country_id].push(d)
    }
    return grouped
  }, [deployments])

  const sortedCountries = useMemo(
    () => Object.keys(deploymentsByCountry).sort(sortCountries),
    [deploymentsByCountry]
  )

  const totalDeployments = useMemo(
    () => deployments.reduce((sum, d) => sum + d.count, 0),
    [deployments]
  )

  /* ---- Render: loading / error ---- */

  if (loading) {
    return (
      <div className="py-8 text-center">
        <p className="font-body text-body-sm text-text-secondary">Loading map data...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="py-8 text-center">
        <p className="font-body text-body-sm text-danger">{error}</p>
      </div>
    )
  }

  /* ---- Render ---- */

  return (
    <div className="space-y-10">
      {/* ================================================================== */}
      {/*  ZONES SECTION                                                      */}
      {/* ================================================================== */}
      <section>
        <h3 className="font-heading text-h3 text-text-primary mb-1">Zones</h3>
        <p className="font-body text-caption text-text-secondary mb-4">
          {zones.length} zones across {theaterOrder.length} theater{theaterOrder.length !== 1 ? 's' : ''}
        </p>

        {theaterOrder.map((theater) => {
          const theaterZones = zonesByTheater[theater] ?? []
          return (
            <div key={theater} className="mb-6">
              <h4 className="font-heading text-h3 text-text-primary mb-2">
                {THEATER_LABELS[theater] ?? cap(theater.replace(/_/g, ' '))}
                <span className="font-body text-caption text-text-secondary ml-2">
                  ({theaterZones.length})
                </span>
              </h4>
              <div className="overflow-x-auto">
                <table className="w-full text-left">
                  <thead>
                    <tr className="border-b border-border">
                      <th className="font-body text-caption text-text-secondary py-2 pr-4">Zone ID</th>
                      <th className="font-body text-caption text-text-secondary py-2 pr-4">Display Name</th>
                      <th className="font-body text-caption text-text-secondary py-2 pr-4">Type</th>
                      <th className="font-body text-caption text-text-secondary py-2 pr-4">Owner</th>
                      <th className="font-body text-caption text-text-secondary py-2 pr-4">Controlled By</th>
                      <th className="font-body text-caption text-text-secondary py-2 pr-4 text-center">Chokepoint</th>
                      <th className="font-body text-caption text-text-secondary py-2 text-center">Die Hard</th>
                    </tr>
                  </thead>
                  <tbody>
                    {theaterZones.map((z) => (
                      <tr key={z.id} className="border-b border-border/50 hover:bg-card/50">
                        <td className="font-data text-data text-text-primary py-2 pr-4">{z.id}</td>
                        <td className="font-body text-body-sm text-text-primary py-2 pr-4">{z.display_name}</td>
                        <td className="py-2 pr-4">
                          <span className={`font-body text-caption px-2 py-0.5 rounded ${zoneTypeClasses(z.type)}`}>
                            {z.type.replace(/_/g, ' ')}
                          </span>
                        </td>
                        <td className="font-body text-body-sm text-text-primary py-2 pr-4">
                          {z.owner ? cap(z.owner) : '—'}
                        </td>
                        <td className="font-body text-body-sm text-text-primary py-2 pr-4">
                          {z.controlled_by ? cap(z.controlled_by) : '—'}
                        </td>
                        <td className="font-data text-data text-center py-2 pr-4">
                          {z.is_chokepoint ? (
                            <span className="text-amber-400">Yes</span>
                          ) : (
                            <span className="text-text-secondary">—</span>
                          )}
                        </td>
                        <td className="font-data text-data text-center py-2">
                          {z.die_hard ? (
                            <span className="text-danger">Yes</span>
                          ) : (
                            <span className="text-text-secondary">—</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )
        })}
      </section>

      {/* ================================================================== */}
      {/*  DEPLOYMENTS SECTION                                                 */}
      {/* ================================================================== */}
      <section>
        <h3 className="font-heading text-h3 text-text-primary mb-1">Deployments</h3>
        <p className="font-body text-caption text-text-secondary mb-4">
          {totalDeployments} total units across {sortedCountries.length} countries
        </p>

        {sortedCountries.length === 0 ? (
          <p className="font-body text-body-sm text-text-secondary">No deployments found.</p>
        ) : (
          <div className="space-y-6">
            {sortedCountries.map((countryId) => {
              const countryDeps = deploymentsByCountry[countryId] ?? []
              const countryTotal = countryDeps.reduce((sum, d) => sum + d.count, 0)
              return (
                <div key={countryId}>
                  <h4 className="font-heading text-h3 text-text-primary mb-2">
                    {cap(countryId)}
                    <span className="font-data text-data text-text-secondary ml-2">
                      ({countryTotal} units)
                    </span>
                  </h4>
                  <div className="overflow-x-auto">
                    <table className="w-full text-left">
                      <thead>
                        <tr className="border-b border-border">
                          <th className="font-body text-caption text-text-secondary py-2 pr-4">Unit Type</th>
                          <th className="font-body text-caption text-text-secondary py-2 pr-4 text-right">Count</th>
                          <th className="font-body text-caption text-text-secondary py-2">Zone</th>
                        </tr>
                      </thead>
                      <tbody>
                        {countryDeps.map((d) => (
                          <tr key={d.id} className="border-b border-border/50 hover:bg-card/50">
                            <td className="font-body text-body-sm text-text-primary py-2 pr-4">
                              {UNIT_TYPE_LABELS[d.unit_type] ?? d.unit_type.replace(/_/g, ' ')}
                            </td>
                            <td className="font-data text-data text-text-primary py-2 pr-4 text-right">
                              {d.count}
                            </td>
                            <td className="font-data text-data text-text-secondary py-2">
                              {d.zone_id}
                            </td>
                          </tr>
                        ))}
                        {/* Summary row */}
                        <tr className="border-t border-border">
                          <td className="font-body text-body-sm text-text-primary font-medium py-2 pr-4">
                            Total
                          </td>
                          <td className="font-data text-data text-action font-medium py-2 pr-4 text-right">
                            {countryTotal}
                          </td>
                          <td className="py-2" />
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>
              )
            })}

            {/* Overall summary */}
            <div className="bg-base border border-border rounded-lg p-4">
              <div className="flex items-center justify-between">
                <span className="font-body text-body-sm text-text-primary font-medium">
                  Total Deployments (all countries)
                </span>
                <span className="font-data text-data text-action font-medium">
                  {totalDeployments} units
                </span>
              </div>
            </div>
          </div>
        )}
      </section>
    </div>
  )
}
