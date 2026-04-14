/**
 * TabGeneral — template metadata editor (name, version, status, description).
 */

import { useState, useEffect } from 'react'
import type { SimTemplate } from '@/lib/queries'
import {
  getTemplateCountries,
  getTemplateRoles,
  getTemplateOrganizations,
  getTemplateZones,
  getTemplateDeployments,
} from '@/lib/queries'

interface TabGeneralProps {
  template: SimTemplate
  onSave: (updates: Partial<SimTemplate>) => Promise<void>
}

const STATUS_OPTIONS = ['draft', 'published', 'deprecated'] as const

export function TabGeneral({ template, onSave }: TabGeneralProps) {
  const [name, setName] = useState(template.name)
  const [version, setVersion] = useState(template.version)
  const [description, setDescription] = useState(template.description ?? '')
  const [status, setStatus] = useState(template.status)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  // Template statistics (read-only summary)
  const [stats, setStats] = useState<{
    countries: number
    roles: number
    organizations: number
    zones: { total: number; global: number; eastern_ereb: number; mashriq: number }
    deployments: number
  } | null>(null)

  useEffect(() => {
    const loadStats = async () => {
      try {
        const [countries, roles, orgs, zones, deployments] = await Promise.all([
          getTemplateCountries(),
          getTemplateRoles(),
          getTemplateOrganizations(),
          getTemplateZones(),
          getTemplateDeployments(),
        ])
        setStats({
          countries: countries.length,
          roles: roles.length,
          organizations: orgs.length,
          zones: {
            total: zones.length,
            global: zones.filter((z) => z.theater === 'global').length,
            eastern_ereb: zones.filter((z) => z.theater === 'eastern_ereb').length,
            mashriq: zones.filter((z) => z.theater === 'mashriq').length,
          },
          deployments: deployments.reduce((sum, d) => sum + d.count, 0),
        })
      } catch (e) {
        console.error('Failed to load template stats:', e)
      }
    }
    loadStats()
  }, [])

  const hasChanges =
    name !== template.name ||
    version !== template.version ||
    description !== (template.description ?? '') ||
    status !== template.status

  const handleSave = async () => {
    setSaving(true)
    setSaved(false)
    try {
      await onSave({
        name,
        version,
        description: description || null,
        status,
      })
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-6 max-w-2xl">
      <h3 className="font-heading text-h3 text-text-primary">
        General Settings
      </h3>

      {/* Template Name */}
      <div>
        <label className="block font-body text-body-sm text-text-secondary mb-1">
          Template Name
        </label>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="w-full bg-base border border-border rounded px-3 py-2 font-body text-body text-text-primary focus:outline-none focus:border-action"
        />
      </div>

      {/* Version */}
      <div>
        <label className="block font-body text-body-sm text-text-secondary mb-1">
          Version
        </label>
        <input
          type="text"
          value={version}
          onChange={(e) => setVersion(e.target.value)}
          className="w-full bg-base border border-border rounded px-3 py-2 font-body text-body text-text-primary focus:outline-none focus:border-action"
          placeholder="e.g. 1.0"
        />
        <p className="font-body text-caption text-text-secondary mt-1">
          Code: {template.code}
        </p>
      </div>

      {/* Status */}
      <div>
        <label className="block font-body text-body-sm text-text-secondary mb-1">
          Status
        </label>
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          className="w-full bg-base border border-border rounded px-3 py-2 font-body text-body text-text-primary focus:outline-none focus:border-action"
        >
          {STATUS_OPTIONS.map((opt) => (
            <option key={opt} value={opt}>
              {opt.charAt(0).toUpperCase() + opt.slice(1)}
            </option>
          ))}
        </select>
      </div>

      {/* Description */}
      <div>
        <label className="block font-body text-body-sm text-text-secondary mb-1">
          Description
        </label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={4}
          className="w-full bg-base border border-border rounded px-3 py-2 font-body text-body text-text-primary focus:outline-none focus:border-action resize-y"
          placeholder="Optional description of this template..."
        />
      </div>

      {/* Template Statistics */}
      {stats && (
        <div className="border border-border rounded-lg p-5 bg-base">
          <h3 className="font-heading text-h3 text-text-primary mb-4">
            Template Summary
          </h3>
          <div className="grid grid-cols-3 gap-6">
            <StatCard label="Countries" value={stats.countries} />
            <StatCard label="Roles" value={stats.roles} />
            <StatCard label="Organizations" value={stats.organizations} />
            <StatCard
              label="Default Rounds"
              value={template.schedule_defaults?.default_rounds ?? 8}
            />
            <StatCard label="Total Units" value={stats.deployments} />
            <StatCard label="Total Zones" value={stats.zones.total} />
          </div>
          <div className="mt-4 pt-3 border-t border-border">
            <p className="font-body text-caption text-text-secondary mb-2">
              Map Structure
            </p>
            <div className="flex gap-6">
              <span className="font-body text-body-sm text-text-primary">
                Global: <span className="font-data text-data">10x20</span>{' '}
                <span className="text-text-secondary">({stats.zones.global} zones)</span>
              </span>
              <span className="font-body text-body-sm text-text-primary">
                Eastern Ereb: <span className="font-data text-data">10x10</span>{' '}
                <span className="text-text-secondary">({stats.zones.eastern_ereb} zones)</span>
              </span>
              <span className="font-body text-body-sm text-text-primary">
                Mashriq: <span className="font-data text-data">10x10</span>{' '}
                <span className="text-text-secondary">({stats.zones.mashriq} zones)</span>
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Save */}
      <div className="flex items-center gap-3">
        <button
          onClick={handleSave}
          disabled={!hasChanges || saving}
          className={`font-body text-body-sm font-medium py-2 px-6 rounded transition-opacity ${
            hasChanges && !saving
              ? 'bg-action text-white hover:opacity-90'
              : 'bg-action/40 text-white/60 cursor-not-allowed'
          }`}
        >
          {saving ? 'Saving...' : 'Save'}
        </button>
        {saved && (
          <span className="font-body text-caption text-success">Saved</span>
        )}
        {hasChanges && !saving && !saved && (
          <span className="font-body text-caption text-warning">
            Unsaved changes
          </span>
        )}
      </div>
    </div>
  )
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <p className="font-body text-caption text-text-secondary">{label}</p>
      <p className="font-data text-data-lg text-text-primary">{value}</p>
    </div>
  )
}
