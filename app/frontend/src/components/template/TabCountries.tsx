/**
 * TabCountries — Template Editor tab for viewing and editing all 20 countries.
 * Loads from the reference sim_run, displays in accordion with grouped editable fields.
 */

import { useState, useEffect, useCallback, useMemo } from 'react'
import {
  getTemplateCountries,
  updateCountry,
  createCountry,
  deleteCountry,
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

const REGIME_OPTIONS = ['democratic', 'authoritarian', 'hybrid', 'theocratic'] as const
const TEAM_TYPE_OPTIONS = ['large_team', 'mid_team', 'solo'] as const
const OPEC_PRODUCTION_OPTIONS = ['min', 'low', 'normal', 'high', 'max', 'na'] as const

/* -------------------------------------------------------------------------- */
/*  Helpers                                                                    */
/* -------------------------------------------------------------------------- */

function capitalize(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1)
}

function formatGdp(v: number): string {
  if (v >= 1_000) return `${(v / 1_000).toFixed(1)}T`
  return `${v.toFixed(0)}B`
}

function sortCountries(countries: Country[]): Country[] {
  return [...countries].sort((a, b) => {
    const ia = COUNTRY_ORDER.indexOf(a.id)
    const ib = COUNTRY_ORDER.indexOf(b.id)
    if (ia >= 0 && ib >= 0) return ia - ib
    if (ia >= 0) return -1
    if (ib >= 0) return 1
    return a.id.localeCompare(b.id)
  })
}

function totalMilitary(c: Country): number {
  return c.mil_ground + c.mil_naval + c.mil_tactical_air + c.mil_strategic_missiles + c.mil_air_defense
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
/*  Add Country inline form                                                    */
/* -------------------------------------------------------------------------- */

interface AddCountryFormProps {
  onCreated: () => void
  onCancel: () => void
}

function AddCountryForm({ onCreated, onCancel }: AddCountryFormProps) {
  const [newId, setNewId] = useState('')
  const [newName, setNewName] = useState('')
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleCreate = async () => {
    const cleanId = newId.trim().toLowerCase().replace(/\s+/g, '_')
    const cleanName = newName.trim()
    if (!cleanId || !cleanName) {
      setError('Both ID and Name are required')
      return
    }
    setCreating(true)
    setError(null)
    try {
      await createCountry({
        id: cleanId,
        sim_name: cleanName,
        regime_type: 'democratic',
        team_type: 'solo',
        team_size_min: 1,
        team_size_max: 1,
        gdp: 0,
        stability: 5,
        political_support: 50,
      })
      onCreated()
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to create country'
      setError(message)
    } finally {
      setCreating(false)
    }
  }

  return (
    <div className="flex items-end gap-3 p-4 bg-card border border-border rounded-lg mb-4">
      <div className="flex flex-col gap-1">
        <label className="font-body text-caption text-text-secondary">Country ID</label>
        <input
          type="text"
          value={newId}
          onChange={(e) => setNewId(e.target.value.toLowerCase().replace(/\s+/g, ''))}
          placeholder="e.g. arcadia"
          className="font-data text-data bg-base border border-border rounded px-2 py-1.5 text-text-primary focus:border-action focus:outline-none w-40"
        />
      </div>
      <div className="flex flex-col gap-1">
        <label className="font-body text-caption text-text-secondary">Country Name</label>
        <input
          type="text"
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          placeholder="e.g. Arcadia"
          className="font-body text-body-sm bg-base border border-border rounded px-2 py-1.5 text-text-primary focus:border-action focus:outline-none w-48"
        />
      </div>
      <button
        onClick={handleCreate}
        disabled={creating}
        className="font-body text-body-sm font-medium bg-action text-white px-4 py-1.5 rounded hover:bg-action/90 transition-colors disabled:opacity-50"
      >
        {creating ? 'Creating...' : 'Create'}
      </button>
      <button
        onClick={onCancel}
        className="font-body text-body-sm text-text-secondary px-3 py-1.5 rounded hover:text-text-primary transition-colors"
      >
        Cancel
      </button>
      {error && (
        <span className="font-body text-caption text-danger">{error}</span>
      )}
    </div>
  )
}

/* -------------------------------------------------------------------------- */
/*  Country editor (expanded panel)                                            */
/* -------------------------------------------------------------------------- */

interface CountryEditorProps {
  country: Country
  onSave: (updated: Country) => Promise<void>
  onDelete: (id: string) => Promise<void>
}

function CountryEditor({ country, onSave, onDelete }: CountryEditorProps) {
  const [draft, setDraft] = useState<Country>({ ...country })
  const [saving, setSaving] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; msg: string } | null>(null)

  /** Reset draft when the country prop changes (e.g. after re-fetch). */
  useEffect(() => {
    setDraft({ ...country })
  }, [country])

  const set = useCallback(<K extends keyof Country>(key: K, value: Country[K]) => {
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
    const confirmed = window.confirm(
      `Delete country "${country.sim_name}" (${country.id})? This action cannot be undone.`
    )
    if (!confirmed) return

    setDeleting(true)
    setFeedback(null)
    try {
      await onDelete(country.id)
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Delete failed'
      setFeedback({ type: 'error', msg: message })
      setDeleting(false)
    }
  }

  const sectorSum = draft.sector_resources + draft.sector_industry + draft.sector_services + draft.sector_technology

  return (
    <div className="px-4 py-4 space-y-2">
      {/* Identity */}
      <SectionHeader title="Identity" />
      <div className="grid grid-cols-2 gap-4">
        <TextField label="sim_name" value={draft.sim_name} onChange={(v) => set('sim_name', v)} />
        <TextField label="parallel" value={draft.parallel} onChange={(v) => set('parallel', v)} />
        <SelectField label="regime_type" value={draft.regime_type} options={REGIME_OPTIONS} onChange={(v) => set('regime_type', v)} />
        <SelectField label="team_type" value={draft.team_type} options={TEAM_TYPE_OPTIONS} onChange={(v) => set('team_type', v)} />
        <NumberField label="team_size_min" value={draft.team_size_min} onChange={(v) => set('team_size_min', v)} min={1} />
        <NumberField label="team_size_max" value={draft.team_size_max} onChange={(v) => set('team_size_max', v)} min={1} />
      </div>
      <div className="mt-2">
        <CheckboxField label="ai_default" checked={draft.ai_default} onChange={(v) => set('ai_default', v)} />
      </div>

      {/* Economic */}
      <SectionHeader title="Economic" />
      <div className="grid grid-cols-2 gap-4">
        <NumberField label="gdp" value={draft.gdp} onChange={(v) => set('gdp', v)} step={0.01} />
        <NumberField label="gdp_growth_base" value={draft.gdp_growth_base} onChange={(v) => set('gdp_growth_base', v)} step={0.001} />
        <NumberField label="tax_rate" value={draft.tax_rate} onChange={(v) => set('tax_rate', v)} step={0.001} />
        <NumberField label="treasury" value={draft.treasury} onChange={(v) => set('treasury', v)} step={0.01} />
        <NumberField label="inflation" value={draft.inflation} onChange={(v) => set('inflation', v)} step={0.01} />
        <NumberField label="trade_balance" value={draft.trade_balance} onChange={(v) => set('trade_balance', v)} step={0.01} />
      </div>
      <div className="grid grid-cols-2 gap-4 mt-3">
        <NumberField label="sector_resources" value={draft.sector_resources} onChange={(v) => set('sector_resources', v)} />
        <NumberField label="sector_industry" value={draft.sector_industry} onChange={(v) => set('sector_industry', v)} />
        <NumberField label="sector_services" value={draft.sector_services} onChange={(v) => set('sector_services', v)} />
        <NumberField label="sector_technology" value={draft.sector_technology} onChange={(v) => set('sector_technology', v)} />
      </div>
      <p className="font-data text-data text-text-secondary mt-1">
        Sector sum: <span className={sectorSum === 100 ? 'text-success' : 'text-warning'}>{sectorSum}%</span>
      </p>
      <div className="grid grid-cols-2 gap-4 mt-3">
        <div className="flex flex-col gap-2">
          <CheckboxField label="oil_producer" checked={draft.oil_producer} onChange={(v) => set('oil_producer', v)} />
          <CheckboxField label="opec_member" checked={draft.opec_member} onChange={(v) => set('opec_member', v)} />
        </div>
        <div className="flex flex-col gap-4">
          <SelectField label="opec_production" value={draft.opec_production} options={OPEC_PRODUCTION_OPTIONS} onChange={(v) => set('opec_production', v)} />
          <NumberField label="oil_production_mbpd" value={draft.oil_production_mbpd} onChange={(v) => set('oil_production_mbpd', v)} step={0.01} />
        </div>
      </div>
      <div className="grid grid-cols-2 gap-4 mt-3">
        <NumberField label="formosa_dependency" value={draft.formosa_dependency} onChange={(v) => set('formosa_dependency', v)} step={0.001} />
        <NumberField label="debt_burden" value={draft.debt_burden} onChange={(v) => set('debt_burden', v)} step={0.01} />
        <NumberField label="debt_ratio" value={draft.debt_ratio} onChange={(v) => set('debt_ratio', v)} step={0.01} />
        <NumberField label="social_baseline" value={draft.social_baseline} onChange={(v) => set('social_baseline', v)} step={0.001} />
        <NumberField label="sanctions_coefficient" value={draft.sanctions_coefficient} onChange={(v) => set('sanctions_coefficient', v)} step={0.0001} />
        <NumberField label="tariff_coefficient" value={draft.tariff_coefficient} onChange={(v) => set('tariff_coefficient', v)} step={0.0001} />
      </div>

      {/* Military */}
      <SectionHeader title="Military" />
      <div className="grid grid-cols-2 gap-4">
        <NumberField label="mil_ground" value={draft.mil_ground} onChange={(v) => set('mil_ground', v)} />
        <NumberField label="mil_naval" value={draft.mil_naval} onChange={(v) => set('mil_naval', v)} />
        <NumberField label="mil_tactical_air" value={draft.mil_tactical_air} onChange={(v) => set('mil_tactical_air', v)} />
        <NumberField label="mil_strategic_missiles" value={draft.mil_strategic_missiles} onChange={(v) => set('mil_strategic_missiles', v)} />
        <NumberField label="mil_air_defense" value={draft.mil_air_defense} onChange={(v) => set('mil_air_defense', v)} />
      </div>
      <div className="grid grid-cols-2 gap-4 mt-3">
        <NumberField label="prod_cost_ground" value={draft.prod_cost_ground} onChange={(v) => set('prod_cost_ground', v)} step={0.01} />
        <NumberField label="prod_cost_naval" value={draft.prod_cost_naval} onChange={(v) => set('prod_cost_naval', v)} step={0.01} />
        <NumberField label="prod_cost_tactical" value={draft.prod_cost_tactical} onChange={(v) => set('prod_cost_tactical', v)} step={0.01} />
      </div>
      <div className="grid grid-cols-2 gap-4 mt-3">
        <NumberField label="prod_cap_ground" value={draft.prod_cap_ground} onChange={(v) => set('prod_cap_ground', v)} />
        <NumberField label="prod_cap_naval" value={draft.prod_cap_naval} onChange={(v) => set('prod_cap_naval', v)} />
        <NumberField label="prod_cap_tactical" value={draft.prod_cap_tactical} onChange={(v) => set('prod_cap_tactical', v)} />
      </div>
      <div className="grid grid-cols-2 gap-4 mt-3">
        <NumberField label="maintenance_per_unit" value={draft.maintenance_per_unit} onChange={(v) => set('maintenance_per_unit', v)} step={0.01} />
        <NumberField label="strategic_missile_growth" value={draft.strategic_missile_growth} onChange={(v) => set('strategic_missile_growth', v)} />
        <NumberField label="mobilization_pool" value={draft.mobilization_pool} onChange={(v) => set('mobilization_pool', v)} />
      </div>

      {/* Political */}
      <SectionHeader title="Political" />
      <div className="grid grid-cols-2 gap-4">
        <NumberField label="stability" value={draft.stability} onChange={(v) => set('stability', v)} min={0} max={10} step={0.01} />
        <NumberField label="political_support" value={draft.political_support} onChange={(v) => set('political_support', v)} min={0} max={100} step={0.01} />
        <NumberField label="dem_rep_split_dem" value={draft.dem_rep_split_dem} onChange={(v) => set('dem_rep_split_dem', v)} />
        <NumberField label="dem_rep_split_rep" value={draft.dem_rep_split_rep} onChange={(v) => set('dem_rep_split_rep', v)} />
        <NumberField label="war_tiredness" value={draft.war_tiredness} onChange={(v) => set('war_tiredness', v)} step={0.01} />
      </div>

      {/* Technology */}
      <SectionHeader title="Technology" />
      <div className="grid grid-cols-2 gap-4">
        <NumberField label="nuclear_level (0-3)" value={draft.nuclear_level} onChange={(v) => set('nuclear_level', v)} min={0} max={3} />
        <NumberField label="nuclear_rd_progress" value={draft.nuclear_rd_progress} onChange={(v) => set('nuclear_rd_progress', v)} step={0.001} min={0} />
        <NumberField label="ai_level (0-4)" value={draft.ai_level} onChange={(v) => set('ai_level', v)} min={0} max={4} />
        <NumberField label="ai_rd_progress" value={draft.ai_rd_progress} onChange={(v) => set('ai_rd_progress', v)} step={0.001} min={0} />
      </div>

      {/* Geography */}
      <SectionHeader title="Geography" />
      <TextField label="home_zones (comma-separated)" value={draft.home_zones} onChange={(v) => set('home_zones', v)} />

      {/* Save + Delete */}
      <div className="flex items-center justify-between mt-4 pt-3 border-t border-border">
        <div className="flex items-center gap-3">
          <button
            onClick={handleSave}
            disabled={saving}
            className="font-body text-body-sm font-medium bg-action text-white px-4 py-2 rounded hover:bg-action/90 transition-colors disabled:opacity-50"
          >
            {saving ? 'Saving...' : 'Save Country'}
          </button>
          {feedback && (
            <span className={`font-body text-caption ${feedback.type === 'success' ? 'text-success' : 'text-danger'}`}>
              {feedback.msg}
            </span>
          )}
        </div>
        <button
          onClick={handleDelete}
          disabled={deleting}
          className="font-body text-body-sm font-medium text-danger border border-danger/30 px-4 py-2 rounded hover:bg-danger/10 transition-colors disabled:opacity-50"
        >
          {deleting ? 'Deleting...' : 'Delete Country'}
        </button>
      </div>
    </div>
  )
}

/* -------------------------------------------------------------------------- */
/*  Main tab component                                                         */
/* -------------------------------------------------------------------------- */

interface TabCountriesProps {
  templateId: string
}

export function TabCountries({ templateId: _templateId }: TabCountriesProps) {
  const [countries, setCountries] = useState<Country[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [showAddForm, setShowAddForm] = useState(false)

  const loadCountries = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await getTemplateCountries()
      setCountries(data)
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to load countries'
      setError(message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadCountries()
  }, [loadCountries])

  const sorted = useMemo(() => sortCountries(countries), [countries])

  const handleSave = useCallback(async (updated: Country) => {
    await updateCountry(updated.id, updated)
    setCountries((prev) =>
      prev.map((c) => (c.id === updated.id ? updated : c))
    )
  }, [])

  const handleDelete = useCallback(async (id: string) => {
    await deleteCountry(id)
    setCountries((prev) => prev.filter((c) => c.id !== id))
    setExpandedId(null)
  }, [])

  const handleCountryCreated = useCallback(() => {
    setShowAddForm(false)
    loadCountries()
  }, [loadCountries])

  if (loading) {
    return (
      <div className="p-6">
        <p className="font-body text-body-sm text-text-secondary">Loading countries...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6">
        <p className="font-body text-body-sm text-danger">{error}</p>
        <button
          onClick={loadCountries}
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
        <h2 className="font-heading text-h2 text-text-primary">Countries</h2>
        {!showAddForm && (
          <button
            onClick={() => setShowAddForm(true)}
            className="font-body text-body-sm font-medium bg-action text-white px-3 py-1 rounded hover:bg-action/90 transition-colors"
          >
            + Add Country
          </button>
        )}
      </div>
      <p className="font-body text-body-sm text-text-secondary mb-6">
        Edit country configuration data. {sorted.length} countries loaded.
      </p>

      {showAddForm && (
        <AddCountryForm
          onCreated={handleCountryCreated}
          onCancel={() => setShowAddForm(false)}
        />
      )}

      <div className="space-y-2">
        {sorted.map((country) => {
          const isExpanded = expandedId === country.id
          return (
            <div
              key={country.id}
              className="border border-border rounded-lg overflow-hidden"
            >
              {/* Collapsed header row */}
              <button
                onClick={() => setExpandedId(isExpanded ? null : country.id)}
                className="w-full bg-base px-4 py-3 flex items-center justify-between hover:bg-card/50 transition-colors"
              >
                <div className="flex items-center gap-4">
                  <span
                    className={`transition-transform text-text-secondary ${isExpanded ? 'rotate-90' : ''}`}
                  >
                    {'\u25B6'}
                  </span>
                  <h3 className="font-heading text-h3 text-text-primary">
                    {capitalize(country.sim_name)}
                  </h3>
                  <span className="font-body text-caption text-text-secondary">
                    {country.regime_type}
                  </span>
                </div>
                <div className="flex items-center gap-6">
                  <span className="font-data text-data text-text-secondary">
                    GDP {formatGdp(country.gdp)}
                  </span>
                  <span className="font-data text-data text-text-secondary">
                    {totalMilitary(country)} units
                  </span>
                </div>
              </button>

              {/* Expanded editor */}
              {isExpanded && (
                <div className="border-t border-border bg-card">
                  <CountryEditor country={country} onSave={handleSave} onDelete={handleDelete} />
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
