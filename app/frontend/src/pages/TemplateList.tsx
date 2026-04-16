/**
 * TemplateList — lists all sim templates with CRUD actions.
 * Route: /admin/templates
 */

import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Header } from '@/components/Header'
import {
  getTemplates,
  createTemplate,
  deleteTemplate,
  duplicateTemplate,
  type SimTemplate,
} from '@/lib/queries'

export function TemplateList() {
  const navigate = useNavigate()
  const [templates, setTemplates] = useState<SimTemplate[]>([])
  const [loading, setLoading] = useState(true)

  const loadTemplates = async () => {
    try {
      const data = await getTemplates()
      setTemplates(data)
    } catch (e) {
      console.error('Failed to load templates:', e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadTemplates()
  }, [])

  const handleCreate = async () => {
    try {
      const now = new Date()
      const code = `TPL_${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}_${String(now.getHours()).padStart(2, '0')}${String(now.getMinutes()).padStart(2, '0')}`
      const template = await createTemplate({
        code,
        name: 'New Template',
        version: '1.0',
      })
      navigate(`/admin/templates/${template.id}/edit`)
    } catch (e) {
      console.error('Create failed:', e)
    }
  }

  const handleDuplicate = async (tpl: SimTemplate) => {
    try {
      const newTpl = await duplicateTemplate(tpl.id, `${tpl.name} (copy)`)
      setTemplates((prev) => [newTpl, ...prev])
    } catch (e) {
      console.error('Duplicate failed:', e)
    }
  }

  const CANONICAL_TEMPLATE_CODE = 'ttt_v1_0'

  const handleDelete = async (tpl: SimTemplate) => {
    if (tpl.code === CANONICAL_TEMPLATE_CODE) {
      alert('The canonical template cannot be deleted.')
      return
    }
    const typed = prompt(`To delete this template, type its full name:\n\n"${tpl.name}"`)
    if (typed !== tpl.name) {
      if (typed !== null) alert('Name does not match. Deletion cancelled.')
      return
    }
    try {
      await deleteTemplate(tpl.id)
      setTemplates((prev) => prev.filter((t) => t.id !== tpl.id))
    } catch (e) {
      console.error('Delete failed:', e)
    }
  }

  const statusColor = (status: string) => {
    switch (status) {
      case 'draft':
        return 'bg-warning/10 text-warning'
      case 'published':
        return 'bg-success/10 text-success'
      case 'deprecated':
        return 'bg-text-secondary/10 text-text-secondary'
      default:
        return 'bg-base text-text-secondary'
    }
  }

  return (
    <div className="min-h-screen bg-base">
      <Header subtitle="Template Management" />

      <main className="max-w-5xl mx-auto px-6 py-8">
        {/* Title + Create button */}
        <div className="flex items-center justify-between mb-6">
          <h2 className="font-heading text-h2 text-text-primary">
            Simulation Templates
          </h2>
          <button
            onClick={handleCreate}
            className="bg-action text-white font-body text-body-sm font-medium py-2 px-4 rounded hover:opacity-90 transition-opacity"
          >
            Create New Template
          </button>
        </div>

        {/* Template list */}
        {loading ? (
          <p className="font-body text-body-sm text-text-secondary">
            Loading...
          </p>
        ) : templates.length === 0 ? (
          <div className="bg-card border border-border rounded-lg p-8 text-center">
            <p className="font-body text-body text-text-secondary mb-4">
              No templates yet.
            </p>
            <button
              onClick={handleCreate}
              className="bg-action text-white font-body text-body-sm font-medium py-2 px-4 rounded hover:opacity-90 transition-opacity"
            >
              Create Your First Template
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {templates.map((tpl) => (
              <div
                key={tpl.id}
                className="bg-card border border-border rounded-lg p-4 flex items-center justify-between hover:border-action/30 transition-colors cursor-pointer"
                onClick={() => navigate(`/admin/templates/${tpl.id}/edit`)}
              >
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-1">
                    <h3 className="font-heading text-h3 text-text-primary">
                      {tpl.name}
                    </h3>
                    <span className="font-mono text-caption text-text-secondary">
                      v{tpl.version}
                    </span>
                    <span
                      className={`font-body text-caption font-medium px-2 py-0.5 rounded ${statusColor(tpl.status)}`}
                    >
                      {tpl.status}
                    </span>
                  </div>
                  <div className="flex items-center gap-4 font-body text-caption text-text-secondary">
                    <span>{tpl.code}</span>
                    {tpl.description && (
                      <span className="truncate max-w-md">
                        {tpl.description}
                      </span>
                    )}
                    <span>
                      {new Date(tpl.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
                <div
                  className="flex items-center gap-2"
                  onClick={(e) => e.stopPropagation()}
                >
                  <button
                    onClick={() =>
                      navigate(`/admin/templates/${tpl.id}/edit`)
                    }
                    className="font-body text-caption text-action hover:underline px-2 py-1"
                    title="Edit"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => handleDuplicate(tpl)}
                    className="font-body text-caption text-text-secondary hover:text-action px-2 py-1"
                    title="Duplicate"
                  >
                    Duplicate
                  </button>
                  {tpl.code !== CANONICAL_TEMPLATE_CODE ? (
                    <button
                      onClick={() => handleDelete(tpl)}
                      className="font-body text-caption text-danger hover:underline px-2 py-1"
                      title="Delete"
                    >
                      Delete
                    </button>
                  ) : (
                    <span className="font-body text-caption text-text-secondary/50 px-2 py-1" title="Canonical template cannot be deleted">
                      Protected
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}
