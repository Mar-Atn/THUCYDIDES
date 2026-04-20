/**
 * TabSanctionsTariffs — sanctions and tariffs data viewer for the template.
 * Two sub-sections toggled by an internal tab: "Sanctions" | "Tariffs".
 * Read-only display for now. Clean table layout with colored level indicators.
 */

import { useEffect, useState } from 'react'
import {
  getTemplateSanctions,
  getTemplateTariffs,
  type Sanction,
  type Tariff,
} from '@/lib/queries'

/** Capitalize first letter of a country id for display. */
function cap(id: string): string {
  return id.charAt(0).toUpperCase() + id.slice(1)
}

type SubTab = 'sanctions' | 'tariffs'

interface TabSanctionsTariffsProps {
  templateId: string
}

/** Color class for sanction level: negative = green (lifting), 0 = gray, positive = red. */
function sanctionLevelColor(level: number): string {
  if (level < 0) return 'text-success font-semibold'
  if (level === 0) return 'text-text-secondary'
  if (level === 1) return 'text-orange-500 font-semibold'
  if (level === 2) return 'text-red-500 font-semibold'
  return 'text-red-700 font-bold'
}

/** Color class for tariff level: 0 = gray, 1+ = orange/red gradient. */
function tariffLevelColor(level: number): string {
  if (level === 0) return 'text-text-secondary'
  if (level === 1) return 'text-orange-500 font-semibold'
  if (level === 2) return 'text-orange-600 font-semibold'
  return 'text-red-600 font-bold'
}

export function TabSanctionsTariffs({ templateId: _templateId }: TabSanctionsTariffsProps) {
  const [sanctions, setSanctions] = useState<Sanction[]>([])
  const [tariffs, setTariffs] = useState<Tariff[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeSubTab, setActiveSubTab] = useState<SubTab>('sanctions')

  useEffect(() => {
    const load = async () => {
      try {
        const [sData, tData] = await Promise.all([
          getTemplateSanctions(),
          getTemplateTariffs(),
        ])
        setSanctions(sData)
        setTariffs(tData)
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to load sanctions/tariffs')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  if (loading) {
    return (
      <div>
        <h3 className="font-heading text-h3 text-text-primary mb-2">
          Sanctions &amp; Tariffs
        </h3>
        <p className="font-body text-body-sm text-text-secondary">Loading...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div>
        <h3 className="font-heading text-h3 text-text-primary mb-2">
          Sanctions &amp; Tariffs
        </h3>
        <p className="font-body text-body-sm text-danger">{error}</p>
      </div>
    )
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-heading text-h3 text-text-primary">
          Sanctions &amp; Tariffs
        </h3>
        <span className="font-body text-caption text-text-secondary bg-base px-2 py-0.5 rounded">
          Read-only
        </span>
      </div>

      {/* Sub-tab toggle */}
      <div className="flex gap-1 mb-4 border-b border-border pb-px">
        <button
          onClick={() => setActiveSubTab('sanctions')}
          className={`font-body text-body-sm font-medium px-4 py-2 rounded-t transition-colors ${
            activeSubTab === 'sanctions'
              ? 'bg-action text-white'
              : 'text-text-secondary hover:text-text-primary hover:bg-base'
          }`}
        >
          Sanctions ({sanctions.length})
        </button>
        <button
          onClick={() => setActiveSubTab('tariffs')}
          className={`font-body text-body-sm font-medium px-4 py-2 rounded-t transition-colors ${
            activeSubTab === 'tariffs'
              ? 'bg-action text-white'
              : 'text-text-secondary hover:text-text-primary hover:bg-base'
          }`}
        >
          Tariffs ({tariffs.length})
        </button>
      </div>

      {/* Sanctions table */}
      {activeSubTab === 'sanctions' && (
        <SanctionsTable sanctions={sanctions} />
      )}

      {/* Tariffs table */}
      {activeSubTab === 'tariffs' && (
        <TariffsTable tariffs={tariffs} />
      )}
    </div>
  )
}

/* -------------------------------------------------------------------------- */
/*  Sanctions sub-component                                                    */
/* -------------------------------------------------------------------------- */

function SanctionsTable({ sanctions }: { sanctions: Sanction[] }) {
  if (sanctions.length === 0) {
    return (
      <p className="font-body text-body-sm text-text-secondary">
        No sanctions data found.
      </p>
    )
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse border border-border">
        <thead>
          <tr className="bg-base">
            <th className="text-left font-body text-caption font-semibold text-text-secondary px-3 py-2 border border-border">
              Imposer
            </th>
            <th className="text-left font-body text-caption font-semibold text-text-secondary px-3 py-2 border border-border">
              Target
            </th>
            <th className="text-center font-body text-caption font-semibold text-text-secondary px-3 py-2 border border-border w-20">
              Level
            </th>
            <th className="text-left font-body text-caption font-semibold text-text-secondary px-3 py-2 border border-border">
              Notes
            </th>
          </tr>
        </thead>
        <tbody>
          {sanctions.map((s) => (
            <tr key={s.id} className="hover:bg-base/50">
              <td className="font-body text-body-sm text-text-primary px-3 py-2 border border-border whitespace-nowrap">
                {cap(s.imposer_country_code)}
              </td>
              <td className="font-body text-body-sm text-text-primary px-3 py-2 border border-border whitespace-nowrap">
                {cap(s.target_country_code)}
              </td>
              <td className={`font-data text-data text-center px-3 py-2 border border-border ${sanctionLevelColor(s.level)}`}>
                {s.level > 0 ? `+${s.level}` : s.level}
              </td>
              <td className="font-body text-caption text-text-secondary px-3 py-2 border border-border max-w-md">
                {s.notes ?? ''}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

/* -------------------------------------------------------------------------- */
/*  Tariffs sub-component                                                      */
/* -------------------------------------------------------------------------- */

function TariffsTable({ tariffs }: { tariffs: Tariff[] }) {
  if (tariffs.length === 0) {
    return (
      <p className="font-body text-body-sm text-text-secondary">
        No tariffs data found.
      </p>
    )
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse border border-border">
        <thead>
          <tr className="bg-base">
            <th className="text-left font-body text-caption font-semibold text-text-secondary px-3 py-2 border border-border">
              Imposer
            </th>
            <th className="text-left font-body text-caption font-semibold text-text-secondary px-3 py-2 border border-border">
              Target
            </th>
            <th className="text-center font-body text-caption font-semibold text-text-secondary px-3 py-2 border border-border w-20">
              Level
            </th>
            <th className="text-left font-body text-caption font-semibold text-text-secondary px-3 py-2 border border-border">
              Notes
            </th>
          </tr>
        </thead>
        <tbody>
          {tariffs.map((t) => (
            <tr key={t.id} className="hover:bg-base/50">
              <td className="font-body text-body-sm text-text-primary px-3 py-2 border border-border whitespace-nowrap">
                {cap(t.imposer_country_code)}
              </td>
              <td className="font-body text-body-sm text-text-primary px-3 py-2 border border-border whitespace-nowrap">
                {cap(t.target_country_code)}
              </td>
              <td className={`font-data text-data text-center px-3 py-2 border border-border ${tariffLevelColor(t.level)}`}>
                {t.level}
              </td>
              <td className="font-body text-caption text-text-secondary px-3 py-2 border border-border max-w-md">
                {t.notes ?? ''}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
