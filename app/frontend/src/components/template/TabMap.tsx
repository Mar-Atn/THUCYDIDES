/**
 * TabMap — Map viewer and editor for the template.
 * Shows zones grouped by theater with ownership and chokepoint data.
 * Links to the full map editor (test-interface) for visual editing.
 */

import { useEffect, useState } from 'react'
import { getTemplateZones, type Zone } from '@/lib/queries'

function cap(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1)
}

const THEATER_ORDER = ['americas', 'ereb', 'asu', 'pacific', 'eastern_ereb', 'mashriq', 'global']
const THEATER_LABELS: Record<string, string> = {
  americas: 'Americas',
  ereb: 'Europe',
  asu: 'Asia',
  pacific: 'Pacific',
  eastern_ereb: 'Eastern Ereb (Theater)',
  mashriq: 'Mashriq (Theater)',
  global: 'Global',
}

const ZONE_TYPE_STYLE: Record<string, string> = {
  land_home: 'bg-success/10 text-success',
  land_contested: 'bg-warning/10 text-warning',
  sea: 'bg-action/10 text-action',
  chokepoint: 'bg-accent/10 text-accent',
  chokepoint_sea: 'bg-accent/10 text-accent',
}

interface TabMapProps {
  templateId: string
}

export function TabMap({ templateId: _templateId }: TabMapProps) {
  const [zones, setZones] = useState<Zone[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const load = async () => {
      try {
        const data = await getTemplateZones()
        setZones(data)
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to load zones')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  // Group zones by theater
  const zonesByTheater: Record<string, Zone[]> = {}
  for (const z of zones) {
    const t = z.theater || 'global'
    if (!zonesByTheater[t]) zonesByTheater[t] = []
    zonesByTheater[t].push(z)
  }

  const sortedTheaters = Object.keys(zonesByTheater).sort((a, b) => {
    const ia = THEATER_ORDER.indexOf(a)
    const ib = THEATER_ORDER.indexOf(b)
    if (ia >= 0 && ib >= 0) return ia - ib
    if (ia >= 0) return -1
    if (ib >= 0) return 1
    return a.localeCompare(b)
  })

  if (loading) {
    return (
      <div>
        <h3 className="font-heading text-h3 text-text-primary mb-2">Map</h3>
        <p className="font-body text-body-sm text-text-secondary">Loading...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div>
        <h3 className="font-heading text-h3 text-text-primary mb-2">Map</h3>
        <p className="font-body text-body-sm text-danger">{error}</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-heading text-h3 text-text-primary">Map</h3>
          <p className="font-body text-caption text-text-secondary mt-1">
            3 canonical views: Global (10x20) + Eastern Ereb (10x10) + Mashriq (10x10)
          </p>
        </div>
        <a
          href="http://localhost:8080/map"
          target="_blank"
          rel="noopener noreferrer"
          className="bg-action text-white font-body text-body-sm font-medium py-2 px-4 rounded hover:opacity-90 transition-opacity"
        >
          Open Map Editor
        </a>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-base border border-border rounded-lg p-3">
          <p className="font-body text-caption text-text-secondary">Total Zones</p>
          <p className="font-data text-data-lg text-text-primary">{zones.length}</p>
        </div>
        <div className="bg-base border border-border rounded-lg p-3">
          <p className="font-body text-caption text-text-secondary">Land Zones</p>
          <p className="font-data text-data-lg text-text-primary">
            {zones.filter(z => z.type.startsWith('land')).length}
          </p>
        </div>
        <div className="bg-base border border-border rounded-lg p-3">
          <p className="font-body text-caption text-text-secondary">Sea Zones</p>
          <p className="font-data text-data-lg text-text-primary">
            {zones.filter(z => z.type === 'sea').length}
          </p>
        </div>
        <div className="bg-base border border-border rounded-lg p-3">
          <p className="font-body text-caption text-text-secondary">Chokepoints</p>
          <p className="font-data text-data-lg text-text-primary">
            {zones.filter(z => z.is_chokepoint).length}
          </p>
        </div>
      </div>

      {/* Zones by theater */}
      {sortedTheaters.map((theater) => {
        const theaterZones = zonesByTheater[theater]
        return (
          <div key={theater}>
            <h4 className="font-heading text-h3 text-text-primary mb-2">
              {THEATER_LABELS[theater] ?? cap(theater)}
              <span className="font-data text-caption text-text-secondary ml-2">
                ({theaterZones.length} zones)
              </span>
            </h4>
            <div className="overflow-x-auto">
              <table className="w-full border-collapse text-left">
                <thead>
                  <tr className="border-b border-border">
                    <th className="font-body text-caption text-text-secondary px-3 py-2">Zone ID</th>
                    <th className="font-body text-caption text-text-secondary px-3 py-2">Name</th>
                    <th className="font-body text-caption text-text-secondary px-3 py-2">Type</th>
                    <th className="font-body text-caption text-text-secondary px-3 py-2">Owner</th>
                    <th className="font-body text-caption text-text-secondary px-3 py-2">Controlled By</th>
                    <th className="font-body text-caption text-text-secondary px-3 py-2 text-center">Chokepoint</th>
                    <th className="font-body text-caption text-text-secondary px-3 py-2 text-center">Die Hard</th>
                  </tr>
                </thead>
                <tbody>
                  {theaterZones.map((z) => (
                    <tr key={z.id} className="border-b border-border/50 hover:bg-base/50">
                      <td className="font-data text-caption text-text-secondary px-3 py-1.5">{z.id}</td>
                      <td className="font-body text-body-sm text-text-primary px-3 py-1.5">{z.display_name}</td>
                      <td className="px-3 py-1.5">
                        <span className={`font-body text-caption px-1.5 py-0.5 rounded ${ZONE_TYPE_STYLE[z.type] ?? 'bg-base text-text-secondary'}`}>
                          {z.type.replace(/_/g, ' ')}
                        </span>
                      </td>
                      <td className="font-body text-body-sm text-text-primary px-3 py-1.5">
                        {z.owner === 'none' || z.owner === 'sea' ? (
                          <span className="text-text-secondary">{z.owner}</span>
                        ) : cap(z.owner)}
                      </td>
                      <td className="font-body text-body-sm text-text-primary px-3 py-1.5">
                        {z.controlled_by ? cap(z.controlled_by) : '—'}
                      </td>
                      <td className="text-center px-3 py-1.5">
                        {z.is_chokepoint && <span className="font-body text-caption text-accent font-bold">CP</span>}
                      </td>
                      <td className="text-center px-3 py-1.5">
                        {z.die_hard && <span className="font-body text-caption text-danger font-bold">DH</span>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )
      })}
    </div>
  )
}
