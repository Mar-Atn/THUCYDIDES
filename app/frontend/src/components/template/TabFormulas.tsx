/**
 * TabFormulas — display formula_coefficients JSONB from the template.
 * Groups parameters by engine domain (economic, political, military, technology).
 * Read-only display; save is a stretch goal.
 */

import { useState, useEffect, useMemo } from 'react'
import { getTemplate, type SimTemplate } from '@/lib/queries'

/* -------------------------------------------------------------------------- */
/*  Props                                                                      */
/* -------------------------------------------------------------------------- */

interface TabFormulasProps {
  templateId: string
}

/* -------------------------------------------------------------------------- */
/*  Constants                                                                  */
/* -------------------------------------------------------------------------- */

/** Domain grouping keys — order matters for display. */
const DOMAIN_ORDER = ['economic', 'political', 'military', 'technology'] as const
type Domain = (typeof DOMAIN_ORDER)[number]

/** Human-friendly domain titles. */
const DOMAIN_TITLES: Record<Domain, string> = {
  economic: 'Economic Parameters',
  political: 'Political Parameters',
  military: 'Military Parameters',
  technology: 'Technology Parameters',
}

/**
 * Convert a key path like "oil.base_price" into a human-readable label.
 * Replaces underscores with spaces and capitalizes each word.
 */
function keyToLabel(keyPath: string): string {
  return keyPath
    .split('.')
    .map((segment) =>
      segment
        .split('_')
        .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
        .join(' ')
    )
    .join(' / ')
}

/** Flatten a nested object into dot-path key-value pairs. */
function flattenObject(
  obj: Record<string, unknown>,
  prefix = ''
): Array<{ key: string; value: unknown }> {
  const result: Array<{ key: string; value: unknown }> = []
  for (const [k, v] of Object.entries(obj)) {
    const fullKey = prefix ? `${prefix}.${k}` : k
    if (v !== null && typeof v === 'object' && !Array.isArray(v)) {
      result.push(...flattenObject(v as Record<string, unknown>, fullKey))
    } else {
      result.push({ key: fullKey, value: v })
    }
  }
  return result
}

/**
 * Attempt to classify a flat key into a domain.
 * Heuristic: check the first segment of the key path against known domain keywords.
 */
function classifyDomain(key: string): Domain | null {
  const lower = key.toLowerCase()
  // Economic keywords
  if (/^(econom|gdp|oil|trade|tariff|sanction|treasury|inflation|debt|tax|sector|budget|opec|formosa_dep)/.test(lower))
    return 'economic'
  // Political keywords
  if (/^(politic|stability|support|election|regime|war_tired|social|dem_rep|fatherland)/.test(lower))
    return 'political'
  // Military keywords
  if (/^(militar|combat|unit|maintenance|mobiliz|ground|naval|air|missile|defense|nuclear|prod_c|prod_cap|strategic)/.test(lower))
    return 'military'
  // Technology keywords
  if (/^(tech|ai_|cyber|rd|research|innovat)/.test(lower))
    return 'technology'
  return null
}

/* -------------------------------------------------------------------------- */
/*  Component                                                                  */
/* -------------------------------------------------------------------------- */

export function TabFormulas({ templateId }: TabFormulasProps) {
  const [loading, setLoading] = useState(true)
  const [template, setTemplate] = useState<SimTemplate | null>(null)
  const [error, setError] = useState<string | null>(null)

  /* ---- Load template ---- */

  useEffect(() => {
    let cancelled = false
    const load = async () => {
      setLoading(true)
      try {
        const tpl = await getTemplate(templateId)
        if (cancelled) return
        setTemplate(tpl)
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : 'Failed to load template')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => { cancelled = true }
  }, [templateId])

  /* ---- Derived: grouped parameters ---- */

  const grouped = useMemo(() => {
    if (!template?.formula_coefficients) return null

    const raw = template.formula_coefficients
    // Skip metadata keys like _source
    const filtered: Record<string, unknown> = {}
    for (const [k, v] of Object.entries(raw)) {
      if (!k.startsWith('_')) filtered[k] = v
    }

    if (Object.keys(filtered).length === 0) return null

    // Check if the JSONB is already organized by domain (has top-level domain keys)
    const hasTopLevelDomains = DOMAIN_ORDER.some(
      (d) => typeof filtered[d] === 'object' && filtered[d] !== null
    )

    const groups: Record<Domain | 'other', Array<{ key: string; value: unknown }>> = {
      economic: [],
      political: [],
      military: [],
      technology: [],
      other: [],
    }

    if (hasTopLevelDomains) {
      // Pre-organized: each top-level key is a domain
      for (const domain of DOMAIN_ORDER) {
        if (filtered[domain] && typeof filtered[domain] === 'object') {
          groups[domain] = flattenObject(filtered[domain] as Record<string, unknown>)
        }
      }
      // Remaining top-level keys that are not domains
      for (const [k, v] of Object.entries(filtered)) {
        if (!DOMAIN_ORDER.includes(k as Domain)) {
          if (typeof v === 'object' && v !== null && !Array.isArray(v)) {
            groups.other.push(...flattenObject(v as Record<string, unknown>, k))
          } else {
            groups.other.push({ key: k, value: v })
          }
        }
      }
    } else {
      // Flat or unorganized: classify each entry by heuristic
      const flat = flattenObject(filtered)
      for (const entry of flat) {
        const domain = classifyDomain(entry.key)
        groups[domain ?? 'other'].push(entry)
      }
    }

    return groups
  }, [template])

  /* ---- Render: loading / error ---- */

  if (loading) {
    return (
      <div className="py-8 text-center">
        <p className="font-body text-body-sm text-text-secondary">Loading formula parameters...</p>
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

  if (!template) {
    return (
      <div className="py-8 text-center">
        <p className="font-body text-body-sm text-danger">Template not found.</p>
      </div>
    )
  }

  /* ---- Render: empty state ---- */

  if (!grouped) {
    return (
      <div className="space-y-4">
        <h3 className="font-heading text-h3 text-text-primary">Formula Parameters</h3>
        <div className="bg-base border border-border rounded-lg p-6 text-center">
          <p className="font-body text-body-sm text-text-secondary">
            Formula coefficients not yet loaded from engine. They will be populated when the
            engine migration is complete.
          </p>
        </div>
      </div>
    )
  }

  /* ---- Render: parameter groups ---- */

  return (
    <div className="space-y-8">
      <h3 className="font-heading text-h3 text-text-primary">Formula Parameters</h3>
      <div className="bg-warning/10 border border-warning/30 rounded-lg p-4">
        <p className="font-body text-body-sm text-warning">
          These values are currently <strong>hardcoded in the engine</strong> and shown here for reference only.
          They will become configurable per template in a future update.
        </p>
      </div>

      {DOMAIN_ORDER.map((domain) => {
        const entries = grouped[domain]
        if (!entries || entries.length === 0) return null
        return (
          <ParameterGroup
            key={domain}
            title={DOMAIN_TITLES[domain]}
            entries={entries}
          />
        )
      })}

      {/* Uncategorized parameters */}
      {grouped.other.length > 0 && (
        <ParameterGroup
          title="Other Parameters"
          entries={grouped.other}
        />
      )}
    </div>
  )
}

/* -------------------------------------------------------------------------- */
/*  ParameterGroup sub-component                                               */
/* -------------------------------------------------------------------------- */

function ParameterGroup({
  title,
  entries,
}: {
  title: string
  entries: Array<{ key: string; value: unknown }>
}) {
  return (
    <div>
      <h4 className="font-heading text-h3 text-text-primary mb-3">{title}</h4>
      <div className="grid grid-cols-2 gap-x-6 gap-y-3">
        {entries.map(({ key, value }) => (
          <div
            key={key}
            className="flex items-center justify-between border-b border-border/30 pb-2"
          >
            <span className="font-body text-body-sm text-text-secondary">
              {keyToLabel(key)}
            </span>
            <span className="font-data text-data text-text-primary ml-4 shrink-0">
              {formatValue(value)}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

/** Format a parameter value for display. */
function formatValue(value: unknown): string {
  if (value === null || value === undefined) return '—'
  if (typeof value === 'number') {
    // Show up to 4 decimal places, strip trailing zeros
    return Number.isInteger(value) ? String(value) : parseFloat(value.toFixed(4)).toString()
  }
  if (typeof value === 'boolean') return value ? 'Yes' : 'No'
  if (Array.isArray(value)) return `[${value.length} items]`
  return String(value)
}
