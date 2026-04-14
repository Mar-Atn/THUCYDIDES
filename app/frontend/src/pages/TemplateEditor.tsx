/**
 * TemplateEditor — tabbed editor shell for a single template.
 * Route: /admin/templates/:id/edit
 */

import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Header } from '@/components/Header'
import { getTemplate, updateTemplate, type SimTemplate } from '@/lib/queries'
import { TabGeneral } from '@/components/template/TabGeneral'
import { TabCountries } from '@/components/template/TabCountries'
import { TabRoles } from '@/components/template/TabRoles'
import { TabOrganizations } from '@/components/template/TabOrganizations'
import { TabRelationships } from '@/components/template/TabRelationships'
import { TabSanctionsTariffs } from '@/components/template/TabSanctionsTariffs'
import { TabMap } from '@/components/template/TabMap'
import { TabDeployments } from '@/components/template/TabDeployments'
import { TabSchedule } from '@/components/template/TabSchedule'
import { TabFormulas } from '@/components/template/TabFormulas'

const TABS = [
  { key: 'general', label: 'General' },
  { key: 'countries', label: 'Countries' },
  { key: 'roles', label: 'Roles' },
  { key: 'organizations', label: 'Organizations' },
  { key: 'relationships', label: 'Relationships' },
  { key: 'sanctions-tariffs', label: 'Sanctions & Tariffs' },
  { key: 'map', label: 'Map' },
  { key: 'deployments', label: 'Deployments' },
  { key: 'schedule', label: 'Schedule' },
  { key: 'formulas', label: 'Formulas' },
] as const

type TabKey = (typeof TABS)[number]['key']

export function TemplateEditor() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [template, setTemplate] = useState<SimTemplate | null>(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<TabKey>('general')

  useEffect(() => {
    if (!id) return
    const load = async () => {
      try {
        const tpl = await getTemplate(id)
        if (!tpl) {
          navigate('/admin/templates')
          return
        }
        setTemplate(tpl)
      } catch (e) {
        console.error('Failed to load template:', e)
        navigate('/admin/templates')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [id, navigate])

  const handleSaveGeneral = async (updates: Partial<SimTemplate>) => {
    if (!template) return
    try {
      await updateTemplate(template.id, updates)
      setTemplate((prev) => (prev ? { ...prev, ...updates } : prev))
    } catch (e) {
      console.error('Save failed:', e)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-base">
        <Header subtitle="Template Editor" />
        <main className="max-w-6xl mx-auto px-6 py-8">
          <p className="font-body text-body-sm text-text-secondary">
            Loading...
          </p>
        </main>
      </div>
    )
  }

  if (!template) return null

  return (
    <div className="min-h-screen bg-base">
      <Header subtitle={`Template: ${template.name}`} />

      <main className="max-w-6xl mx-auto px-6 py-8">
        {/* Back link */}
        <button
          onClick={() => navigate('/admin/templates')}
          className="font-body text-caption text-text-secondary hover:text-action transition-colors mb-4 inline-block"
        >
          &larr; Back to Templates
        </button>

        {/* Tab bar */}
        <div className="flex flex-wrap gap-1 mb-6 border-b border-border pb-px">
          {TABS.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`font-body text-body-sm font-medium px-4 py-2 rounded-t transition-colors ${
                activeTab === tab.key
                  ? 'bg-action text-white'
                  : 'text-text-secondary hover:text-text-primary hover:bg-card'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab content */}
        <div className="bg-card border border-border rounded-lg p-6">
          {activeTab === 'general' && (
            <TabGeneral template={template} onSave={handleSaveGeneral} />
          )}
          {activeTab === 'countries' && (
            <TabCountries templateId={template.id} />
          )}
          {activeTab === 'roles' && (
            <TabRoles templateId={template.id} />
          )}
          {activeTab === 'organizations' && (
            <TabOrganizations templateId={template.id} />
          )}
          {activeTab === 'relationships' && (
            <TabRelationships templateId={template.id} />
          )}
          {activeTab === 'sanctions-tariffs' && (
            <TabSanctionsTariffs templateId={template.id} />
          )}
          {activeTab === 'map' && (
            <TabMap templateId={template.id} />
          )}
          {activeTab === 'deployments' && (
            <TabDeployments templateId={template.id} />
          )}
          {activeTab === 'schedule' && (
            <TabSchedule templateId={template.id} />
          )}
          {activeTab === 'formulas' && (
            <TabFormulas templateId={template.id} />
          )}
        </div>
      </main>
    </div>
  )
}
