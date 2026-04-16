/**
 * Moderator Dashboard — quick actions + my simulations.
 * M9 Phase A: the moderator's home screen.
 */

import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Header } from '@/components/Header'
import { getSimRuns, deleteSimRun, duplicateSimRun, simAction, type SimRun } from '@/lib/queries'

export function ModeratorDashboard() {
  const navigate = useNavigate()
  const [simRuns, setSimRuns] = useState<SimRun[]>([])
  const [loading, setLoading] = useState(true)

  const loadRuns = async () => {
    try {
      const runs = await getSimRuns()
      setSimRuns(runs)
    } catch (e) {
      console.error('Failed to load sim runs:', e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadRuns()
  }, [])

  const handleDelete = async (id: string, name: string) => {
    const typed = prompt(`To delete this simulation, type its full name:\n\n"${name}"`)
    if (typed !== name) {
      if (typed !== null) alert('Name does not match. Deletion cancelled.')
      return
    }
    try {
      await deleteSimRun(id)
      setSimRuns((prev) => prev.filter((r) => r.id !== id))
    } catch (e) {
      console.error('Delete failed:', e)
    }
  }

  const handleDuplicate = async (run: SimRun) => {
    const newName = `${run.name} (copy)`
    try {
      const newRun = await duplicateSimRun(run.id, newName)
      setSimRuns((prev) => [newRun, ...prev])
    } catch (e) {
      console.error('Duplicate failed:', e)
    }
  }

  const statusColor = (status: string) => {
    switch (status) {
      case 'setup':
        return 'bg-warning/10 text-warning'
      case 'ready':
        return 'bg-action/10 text-action'
      case 'running':
        return 'bg-success/10 text-success'
      case 'completed':
        return 'bg-text-secondary/10 text-text-secondary'
      default:
        return 'bg-base text-text-secondary'
    }
  }

  return (
    <div className="min-h-screen bg-base">
      <Header subtitle="Moderator Dashboard" />

      <main className="max-w-5xl mx-auto px-6 py-8">
        {/* Quick Actions */}
        <section className="mb-8">
          <h2 className="font-heading text-h2 text-text-primary mb-4">
            Quick Actions
          </h2>
          <div className="grid grid-cols-3 gap-4">
            <QuickAction
              title="Create New SIM-Run"
              description="Set up a new simulation from a template"
              onClick={() => navigate('/sim/create')}
            />
            <QuickAction
              title="Manage Templates"
              description="Edit scenario templates and world data"
              onClick={() => navigate('/admin/templates')}
            />
            <QuickAction
              title="AI System Setup"
              description="Configure global LLM models"
              onClick={() => navigate('/admin/ai-setup')}
            />
            <QuickAction
              title="Sim Data Analysis"
              description="Review simulation results"
              onClick={() => {}}
              disabled
            />
            <QuickAction
              title="User Management"
              description="Manage registered users and roles"
              onClick={() => navigate('/admin/users')}
            />
            <QuickAction
              title=""
              description=""
              onClick={() => {}}
              disabled
              hidden
            />
          </div>
        </section>

        {/* My Simulations */}
        <section>
          <h2 className="font-heading text-h2 text-text-primary mb-4">
            My Simulations
          </h2>

          {loading ? (
            <p className="font-body text-body-sm text-text-secondary">
              Loading...
            </p>
          ) : simRuns.length === 0 ? (
            <div className="bg-card border border-border rounded-lg p-8 text-center">
              <p className="font-body text-body text-text-secondary mb-4">
                No simulations yet.
              </p>
              <button
                onClick={() => navigate('/sim/create')}
                className="bg-action text-white font-body text-body-sm font-medium py-2 px-4 rounded hover:opacity-90 transition-opacity"
              >
                Create Your First SIM-Run
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              {simRuns.map((run) => (
                <div
                  key={run.id}
                  className="bg-card border border-border rounded-lg p-4 flex items-center justify-between hover:border-action/30 transition-colors cursor-pointer"
                  onClick={() => navigate(`/sim/${run.id}/live`)}
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-1">
                      <h3 className="font-heading text-h3 text-text-primary">
                        {run.name}
                      </h3>
                      <span
                        className={`font-body text-caption font-medium px-2 py-0.5 rounded ${statusColor(run.status)}`}
                      >
                        {run.status}
                      </span>
                    </div>
                    <div className="flex items-center gap-4 font-body text-caption text-text-secondary">
                      <span>{run.max_rounds} rounds</span>
                      <span>
                        {run.human_participants} human /{' '}
                        {run.ai_participants} AI
                      </span>
                      <span>
                        {new Date(run.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                  <div
                    className="flex items-center gap-2"
                    onClick={(e) => e.stopPropagation()}
                  >
                    {run.status === 'setup' ? (
                      <button
                        onClick={async () => {
                          try {
                            await simAction(run.id, 'pre-start')
                            navigate(`/sim/${run.id}/live`)
                          } catch (e) {
                            console.error('Launch failed:', e)
                            navigate(`/sim/${run.id}/live`)
                          }
                        }}
                        className="font-body text-caption font-medium text-success hover:underline px-2 py-1"
                        title="Launch simulation"
                      >
                        Launch
                      </button>
                    ) : (
                      <button
                        onClick={() => navigate(`/sim/${run.id}/live`)}
                        className="font-body text-caption font-medium text-success hover:underline px-2 py-1"
                        title="Open live dashboard"
                      >
                        Live
                      </button>
                    )}
                    <button
                      onClick={() => navigate(`/sim/${run.id}/edit`)}
                      className="font-body text-caption text-action hover:underline px-2 py-1"
                      title="Edit"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDuplicate(run)}
                      className="font-body text-caption text-text-secondary hover:text-action px-2 py-1"
                      title="Duplicate"
                    >
                      Duplicate
                    </button>
                    <button
                      onClick={() => handleDelete(run.id, run.name)}
                      className="font-body text-caption text-danger hover:underline px-2 py-1"
                      title="Delete"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  )
}

/* -------------------------------------------------------------------------- */
/*  Quick Action Card                                                         */
/* -------------------------------------------------------------------------- */

function QuickAction({
  title,
  description,
  onClick,
  disabled,
  hidden,
}: {
  title: string
  description: string
  onClick: () => void
  disabled?: boolean
  hidden?: boolean
}) {
  if (hidden) {
    return <div className="border border-transparent" />
  }

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`text-left border rounded-lg p-4 transition-colors ${
        disabled
          ? 'border-border bg-base opacity-50 cursor-not-allowed'
          : 'border-border bg-card hover:border-action/40 cursor-pointer'
      }`}
    >
      <h3 className="font-heading text-h3 text-text-primary mb-1">{title}</h3>
      <p className="font-body text-caption text-text-secondary">
        {description}
      </p>
    </button>
  )
}
