/**
 * AI System Setup — global LLM model configuration for the simulation.
 * Moderator selects which models power AI participants, engine, and fallbacks.
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
  { value: 'claude-sonnet-4-20250514', label: 'Claude Sonnet 4' },
  { value: 'claude-haiku-4-5-20251001', label: 'Claude Haiku 4.5' },
  { value: 'gemini-2.5-pro', label: 'Gemini 2.5 Pro' },
  { value: 'gemini-2.5-flash', label: 'Gemini 2.5 Flash' },
  { value: 'gemini-2.5-flash-lite', label: 'Gemini 2.5 Flash Lite' },
]

/** Config keys stored in sim_config with category='llm'. */
const CONFIG_KEYS = {
  participantDecisions: 'ai_participant_decisions',
  participantConversations: 'ai_participant_conversations',
  engineModerator: 'ai_engine_moderator',
  fallback1: 'ai_fallback_1',
  fallback2: 'ai_fallback_2',
} as const

const FIELD_LABELS: Record<string, string> = {
  [CONFIG_KEYS.participantDecisions]: 'AI Participants (decisions)',
  [CONFIG_KEYS.participantConversations]: 'AI Participants (conversations)',
  [CONFIG_KEYS.engineModerator]: 'AI Engine (moderator / judgment)',
  [CONFIG_KEYS.fallback1]: 'Fallback Model 1',
  [CONFIG_KEYS.fallback2]: 'Fallback Model 2',
}

const FIELD_DESCRIPTIONS: Record<string, string> = {
  [CONFIG_KEYS.participantDecisions]:
    'Model used for AI leader strategic decisions and action selection.',
  [CONFIG_KEYS.participantConversations]:
    'Model used for AI leader conversations and negotiations.',
  [CONFIG_KEYS.engineModerator]:
    'Model used for moderator judgment calls, event narration, and resolution.',
  [CONFIG_KEYS.fallback1]:
    'Primary fallback if the assigned model is unavailable.',
  [CONFIG_KEYS.fallback2]:
    'Secondary fallback — last resort.',
}

/** Default model values for new installations. */
const DEFAULTS: Record<string, string> = {
  [CONFIG_KEYS.participantDecisions]: 'claude-sonnet-4-20250514',
  [CONFIG_KEYS.participantConversations]: 'gemini-2.5-flash',
  [CONFIG_KEYS.engineModerator]: 'claude-sonnet-4-20250514',
  [CONFIG_KEYS.fallback1]: 'gemini-2.5-pro',
  [CONFIG_KEYS.fallback2]: 'gemini-2.5-flash-lite',
}

/* -------------------------------------------------------------------------- */
/*  Component                                                                 */
/* -------------------------------------------------------------------------- */

export function AISetup() {
  const navigate = useNavigate()

  const [models, setModels] = useState<Record<string, string>>({ ...DEFAULTS })
  const [templateId, setTemplateId] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [saveMessage, setSaveMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  /* Load template + existing config on mount */
  useEffect(() => {
    const init = async () => {
      try {
        // We need a template_id for sim_config inserts
        const templates = await getTemplates()
        if (templates.length === 0) {
          setError('No templates found. Create a template first before configuring AI settings.')
          setLoading(false)
          return
        }
        setTemplateId(templates[0].id)

        // Load existing LLM config
        const config = await getGlobalConfig('llm')
        if (Object.keys(config).length > 0) {
          setModels((prev) => ({ ...prev, ...config }))
        }
      } catch (e) {
        setError(`Failed to load configuration: ${e instanceof Error ? e.message : String(e)}`)
      } finally {
        setLoading(false)
      }
    }

    init()
  }, [])

  /** Persist all 5 model settings to the DB. */
  const handleSave = async () => {
    if (!templateId) return

    setSaving(true)
    setSaveMessage(null)

    try {
      const keys = Object.values(CONFIG_KEYS)
      for (const key of keys) {
        await setGlobalConfig('llm', key, models[key] ?? '', templateId)
      }
      setSaveMessage('Configuration saved successfully.')
    } catch (e) {
      setSaveMessage(`Save failed: ${e instanceof Error ? e.message : String(e)}`)
    } finally {
      setSaving(false)
    }
  }

  const handleChange = (key: string, value: string) => {
    setModels((prev) => ({ ...prev, [key]: value }))
    setSaveMessage(null)
  }

  /* ---- Render ---- */

  return (
    <div className="min-h-screen bg-base">
      <Header subtitle="AI System Setup" />

      <main className="max-w-3xl mx-auto px-6 py-8">
        {/* Back link */}
        <button
          onClick={() => navigate('/dashboard')}
          className="font-body text-caption text-action hover:underline mb-6 inline-block"
        >
          &larr; Back to Dashboard
        </button>

        {/* Error state */}
        {error && (
          <div className="bg-danger/10 border border-danger/30 rounded-lg p-4 mb-6">
            <p className="font-body text-body-sm text-danger">{error}</p>
          </div>
        )}

        {/* Loading state */}
        {loading && (
          <p className="font-body text-body-sm text-text-secondary">
            Loading configuration...
          </p>
        )}

        {/* Main content */}
        {!loading && !error && (
          <>
            {/* ---- Global Model Configuration ---- */}
            <section className="mb-10">
              <h2 className="font-heading text-h2 text-text-primary mb-2">
                Global Model Configuration
              </h2>
              <p className="font-body text-body-sm text-text-secondary mb-6">
                Select which LLM models power each system function. Changes apply
                to all new simulation runs.
              </p>

              <div className="space-y-4">
                {Object.values(CONFIG_KEYS).map((key) => (
                  <div
                    key={key}
                    className="bg-card border border-border rounded-lg p-4"
                  >
                    <label
                      htmlFor={key}
                      className="block font-heading text-h3 text-text-primary mb-1"
                    >
                      {FIELD_LABELS[key]}
                    </label>
                    <p className="font-body text-caption text-text-secondary mb-3">
                      {FIELD_DESCRIPTIONS[key]}
                    </p>
                    <select
                      id={key}
                      value={models[key] ?? ''}
                      onChange={(e) => handleChange(key, e.target.value)}
                      className="w-full bg-base border border-border rounded px-3 py-2 font-body text-body-sm text-text-primary focus:outline-none focus:border-action transition-colors"
                    >
                      {AVAILABLE_MODELS.map((m) => (
                        <option key={m.value} value={m.value}>
                          {m.label}
                        </option>
                      ))}
                    </select>
                  </div>
                ))}
              </div>

              {/* Save button + feedback */}
              <div className="mt-6 flex items-center gap-4">
                <button
                  onClick={handleSave}
                  disabled={saving}
                  className="bg-action text-white font-body text-body-sm font-medium py-2 px-6 rounded hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {saving ? 'Saving...' : 'Save Configuration'}
                </button>
                {saveMessage && (
                  <span
                    className={`font-body text-body-sm ${
                      saveMessage.startsWith('Save failed')
                        ? 'text-danger'
                        : 'text-success'
                    }`}
                  >
                    {saveMessage}
                  </span>
                )}
              </div>
            </section>

            {/* ---- AI Prompt Management (placeholder) ---- */}
            <section>
              <h2 className="font-heading text-h2 text-text-primary mb-2">
                AI Prompt Management
              </h2>
              <div className="bg-card border border-border rounded-lg p-6">
                <p className="font-body text-body-sm text-text-secondary">
                  Prompt editor coming in M5 (AI Participant module).
                </p>
              </div>
            </section>
          </>
        )}
      </main>
    </div>
  )
}
