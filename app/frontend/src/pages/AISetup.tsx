/**
 * AI System Setup — global AI configuration for the simulation.
 *
 * Settings stored in sim_config table:
 * - category='ai': model selection + assertiveness
 * - Read by ai_config.py at runtime
 *
 * All AI participants across all sim runs use these settings.
 */

import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Header } from '@/components/Header'
import { getGlobalConfig, setGlobalConfig, getTemplates } from '@/lib/queries'

/* -------------------------------------------------------------------------- */
/*  Model Definitions                                                         */
/* -------------------------------------------------------------------------- */

interface ModelOption {
  value: string
  label: string
}

const AVAILABLE_MODELS: ModelOption[] = [
  { value: 'claude-sonnet-4-6', label: 'Claude Sonnet 4.6' },
  { value: 'claude-opus-4-6', label: 'Claude Opus 4.6' },
  { value: 'claude-haiku-4-5-20251001', label: 'Claude Haiku 4.5' },
]

/**
 * Config keys stored in sim_config with category='ai'.
 * These MUST match the keys in ai_config.py exactly.
 */
const CONFIG_KEYS = {
  modelDecisions: 'model_decisions',
  modelConversations: 'model_conversations',
  assertiveness: 'assertiveness',
} as const

const FIELD_LABELS: Record<string, string> = {
  [CONFIG_KEYS.modelDecisions]: 'AI Participants — Decisions',
  [CONFIG_KEYS.modelConversations]: 'AI Participants — Conversations',
  [CONFIG_KEYS.assertiveness]: 'Global Assertiveness Dial',
}

const FIELD_DESCRIPTIONS: Record<string, string> = {
  [CONFIG_KEYS.modelDecisions]:
    'Model for strategic decisions, action selection, and tool use.',
  [CONFIG_KEYS.modelConversations]:
    'Model for bilateral meetings and negotiations.',
  [CONFIG_KEYS.assertiveness]:
    'Shifts all AI participants toward cooperation (1) or competition (10). Default: 5 (balanced).',
}

/** Default values. Must match ai_config.py defaults. */
const DEFAULTS: Record<string, string> = {
  [CONFIG_KEYS.modelDecisions]: 'claude-sonnet-4-6',
  [CONFIG_KEYS.modelConversations]: 'claude-sonnet-4-6',
  [CONFIG_KEYS.assertiveness]: '5',
}

/* -------------------------------------------------------------------------- */
/*  Component                                                                 */
/* -------------------------------------------------------------------------- */

export function AISetup() {
  const navigate = useNavigate()

  const [config, setConfig] = useState<Record<string, string>>({ ...DEFAULTS })
  const [templateId, setTemplateId] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [saveMessage, setSaveMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  /* Load template + existing config on mount */
  useEffect(() => {
    const init = async () => {
      try {
        const templates = await getTemplates()
        if (templates.length === 0) {
          setError('No templates found. Create a template first.')
          setLoading(false)
          return
        }
        setTemplateId(templates[0].id)

        // Load existing AI config (category='ai')
        const existing = await getGlobalConfig('ai')
        if (Object.keys(existing).length > 0) {
          setConfig((prev) => ({ ...prev, ...existing }))
        }
      } catch (e) {
        setError(`Failed to load: ${e instanceof Error ? e.message : String(e)}`)
      } finally {
        setLoading(false)
      }
    }
    init()
  }, [])

  /** Save all settings to DB. */
  const handleSave = async () => {
    if (!templateId) return
    setSaving(true)
    setSaveMessage(null)
    try {
      for (const key of Object.values(CONFIG_KEYS)) {
        await setGlobalConfig('ai', key, config[key] ?? '', templateId)
      }
      setSaveMessage('Configuration saved.')
    } catch (e) {
      setSaveMessage(`Save failed: ${e instanceof Error ? e.message : String(e)}`)
    } finally {
      setSaving(false)
    }
  }

  const handleChange = (key: string, value: string) => {
    setConfig((prev) => ({ ...prev, [key]: value }))
    setSaveMessage(null)
  }

  const assertiveness = parseInt(config[CONFIG_KEYS.assertiveness] || '5', 10)
  const assertivenessLabel =
    assertiveness <= 2 ? 'Very Cooperative' :
    assertiveness <= 4 ? 'Cooperative' :
    assertiveness === 5 ? 'Balanced' :
    assertiveness <= 7 ? 'Assertive' :
    assertiveness <= 9 ? 'Very Assertive' :
    'Maximum Competition'

  return (
    <div className="min-h-screen bg-base">
      <Header subtitle="AI System Setup" />

      <main className="max-w-3xl mx-auto px-6 py-8">
        <button
          onClick={() => navigate('/dashboard')}
          className="font-body text-caption text-action hover:underline mb-6 inline-block"
        >
          &larr; Back to Dashboard
        </button>

        {error && (
          <div className="bg-danger/10 border border-danger/30 rounded-lg p-4 mb-6">
            <p className="font-body text-body-sm text-danger">{error}</p>
          </div>
        )}

        {loading && <p className="font-body text-body-sm text-text-secondary">Loading...</p>}

        {!loading && !error && (
          <>
            {/* ---- Model Selection ---- */}
            <section className="mb-10">
              <h2 className="font-heading text-h2 text-text-primary mb-2">
                AI Model Configuration
              </h2>
              <p className="font-body text-body-sm text-text-secondary mb-6">
                Select which Claude models power AI participants. Applies globally across all simulation runs.
              </p>

              <div className="space-y-4">
                {[CONFIG_KEYS.modelDecisions, CONFIG_KEYS.modelConversations].map((key) => (
                  <div key={key} className="bg-card border border-border rounded-lg p-4">
                    <label htmlFor={key} className="block font-heading text-h3 text-text-primary mb-1">
                      {FIELD_LABELS[key]}
                    </label>
                    <p className="font-body text-caption text-text-secondary mb-3">
                      {FIELD_DESCRIPTIONS[key]}
                    </p>
                    <select
                      id={key}
                      value={config[key] ?? ''}
                      onChange={(e) => handleChange(key, e.target.value)}
                      className="w-full bg-base border border-border rounded px-3 py-2 font-body text-body-sm text-text-primary focus:outline-none focus:border-action transition-colors"
                    >
                      {AVAILABLE_MODELS.map((m) => (
                        <option key={m.value} value={m.value}>{m.label}</option>
                      ))}
                    </select>
                  </div>
                ))}
              </div>
            </section>

            {/* ---- Assertiveness Dial ---- */}
            <section className="mb-10">
              <h2 className="font-heading text-h2 text-text-primary mb-2">
                Behavior Configuration
              </h2>

              <div className="bg-card border border-border rounded-lg p-4">
                <label htmlFor="assertiveness" className="block font-heading text-h3 text-text-primary mb-1">
                  {FIELD_LABELS[CONFIG_KEYS.assertiveness]}
                </label>
                <p className="font-body text-caption text-text-secondary mb-4">
                  {FIELD_DESCRIPTIONS[CONFIG_KEYS.assertiveness]}
                </p>

                <div className="flex items-center gap-4">
                  <span className="font-body text-caption text-text-secondary w-24">Cooperative</span>
                  <input
                    id="assertiveness"
                    type="range"
                    min="1"
                    max="10"
                    value={assertiveness}
                    onChange={(e) => handleChange(CONFIG_KEYS.assertiveness, e.target.value)}
                    className="flex-1 h-2 bg-border rounded-lg appearance-none cursor-pointer accent-action"
                  />
                  <span className="font-body text-caption text-text-secondary w-24 text-right">Competitive</span>
                </div>
                <div className="text-center mt-2">
                  <span className="font-data text-h3 text-action">{assertiveness}</span>
                  <span className="font-body text-caption text-text-secondary ml-2">— {assertivenessLabel}</span>
                </div>
              </div>
            </section>

            {/* ---- Save ---- */}
            <div className="flex items-center gap-4">
              <button
                onClick={handleSave}
                disabled={saving}
                className="bg-action text-white font-body text-body-sm font-medium py-2 px-6 rounded hover:opacity-90 transition-opacity disabled:opacity-50"
              >
                {saving ? 'Saving...' : 'Save Configuration'}
              </button>
              {saveMessage && (
                <span className={`font-body text-body-sm ${saveMessage.startsWith('Save failed') ? 'text-danger' : 'text-success'}`}>
                  {saveMessage}
                </span>
              )}
            </div>
          </>
        )}
      </main>
    </div>
  )
}
