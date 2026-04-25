/**
 * AI System Setup — global AI configuration.
 *
 * Settings stored in ai_settings table (global, not per-sim).
 * Two categories:
 *   - Managed agent settings (locked at init): model_decisions, model_conversations, assertiveness
 *   - Stateless API settings (immediate): model_stateless
 */

import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Header } from '@/components/Header'
import { getAISettings, updateAISetting } from '@/lib/queries'

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

interface SettingDef {
  key: string
  label: string
  description: string
  note: string // reinit or immediate
  type: 'model' | 'slider'
  default: string
}

const MANAGED_SETTINGS: SettingDef[] = [
  {
    key: 'model_decisions',
    label: 'AI Participants — Decisions',
    description: 'Model for strategic decisions, action selection, and tool use.',
    note: 'Locked at initialization. Change requires Shutdown → Re-initialize.',
    type: 'model',
    default: 'claude-sonnet-4-6',
  },
  {
    key: 'model_conversations',
    label: 'AI Participants — Conversations',
    description: 'Model for bilateral meetings and negotiations.',
    note: 'Locked at initialization. Change requires Shutdown → Re-initialize.',
    type: 'model',
    default: 'claude-sonnet-4-6',
  },
  {
    key: 'assertiveness',
    label: 'Global Assertiveness Dial',
    description: 'Shifts all AI participants toward cooperation (1) or competition (10). Default: 5 (balanced).',
    note: 'Applied at initialization. Change requires Shutdown → Re-initialize.',
    type: 'slider',
    default: '5',
  },
]

const STATELESS_SETTINGS: SettingDef[] = [
  {
    key: 'model_stateless',
    label: 'Stateless API Calls',
    description: 'Model for intelligence reports, chat assistance, Navigator, and other one-shot calls.',
    note: 'Changes take effect immediately on next API call.',
    type: 'model',
    default: 'claude-sonnet-4-6',
  },
]

/* -------------------------------------------------------------------------- */
/*  Component                                                                 */
/* -------------------------------------------------------------------------- */

export function AISetup() {
  const navigate = useNavigate()

  const [config, setConfig] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState<string | null>(null) // key being saved
  const [saveMessage, setSaveMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  /* Load settings on mount */
  useEffect(() => {
    const init = async () => {
      try {
        const settings = await getAISettings()
        // Merge with defaults
        const merged: Record<string, string> = {}
        for (const s of [...MANAGED_SETTINGS, ...STATELESS_SETTINGS]) {
          merged[s.key] = settings[s.key] || s.default
        }
        setConfig(merged)
      } catch (e) {
        setError(`Failed to load: ${e instanceof Error ? e.message : String(e)}`)
      } finally {
        setLoading(false)
      }
    }
    init()
  }, [])

  /** Save a single setting. */
  const handleSave = async (key: string, value: string) => {
    setSaving(key)
    setSaveMessage(null)
    try {
      const result = await updateAISetting(key, value)
      setSaveMessage(result.message)
    } catch (e) {
      setSaveMessage(`Save failed: ${e instanceof Error ? e.message : String(e)}`)
    } finally {
      setSaving(null)
    }
  }

  const handleChange = (key: string, value: string) => {
    setConfig((prev) => ({ ...prev, [key]: value }))
    setSaveMessage(null)
  }

  /** Save all settings at once. */
  const handleSaveAll = async () => {
    setSaving('all')
    setSaveMessage(null)
    try {
      for (const s of [...MANAGED_SETTINGS, ...STATELESS_SETTINGS]) {
        if (config[s.key]) {
          await updateAISetting(s.key, config[s.key])
        }
      }
      setSaveMessage('All settings saved.')
    } catch (e) {
      setSaveMessage(`Save failed: ${e instanceof Error ? e.message : String(e)}`)
    } finally {
      setSaving(null)
    }
  }

  const assertiveness = parseInt(config['assertiveness'] || '5', 10)
  const assertivenessLabel =
    assertiveness <= 2 ? 'Very Cooperative' :
    assertiveness <= 4 ? 'Cooperative' :
    assertiveness === 5 ? 'Balanced' :
    assertiveness <= 7 ? 'Assertive' :
    assertiveness <= 9 ? 'Very Assertive' :
    'Maximum Competition'

  const renderModelField = (s: SettingDef) => (
    <div key={s.key} className="bg-card border border-border rounded-lg p-4">
      <label htmlFor={s.key} className="block font-heading text-h3 text-text-primary mb-1">
        {s.label}
      </label>
      <p className="font-body text-caption text-text-secondary mb-1">
        {s.description}
      </p>
      <p className="font-body text-caption text-warning/80 mb-3 italic">
        {s.note}
      </p>
      <select
        id={s.key}
        value={config[s.key] ?? ''}
        onChange={(e) => handleChange(s.key, e.target.value)}
        className="w-full bg-base border border-border rounded px-3 py-2 font-body text-body-sm text-text-primary focus:outline-none focus:border-action transition-colors"
      >
        {AVAILABLE_MODELS.map((m) => (
          <option key={m.value} value={m.value}>{m.label}</option>
        ))}
      </select>
    </div>
  )

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
            {/* ---- Managed Agent Settings (locked at init) ---- */}
            <section className="mb-10">
              <h2 className="font-heading text-h2 text-text-primary mb-2">
                Managed Agent Settings
              </h2>
              <p className="font-body text-body-sm text-text-secondary mb-1">
                These settings are applied when AI agents are initialized. They are <strong>locked for the duration of the session</strong>.
              </p>
              <p className="font-body text-caption text-warning/70 mb-6">
                To change: Shutdown AI agents → update settings → Re-initialize. Agent memory notes in DB survive reinitialization.
              </p>

              <div className="space-y-4">
                {MANAGED_SETTINGS.filter(s => s.type === 'model').map(renderModelField)}
              </div>
            </section>

            {/* ---- Assertiveness Dial ---- */}
            <section className="mb-10">
              <h2 className="font-heading text-h2 text-text-primary mb-2">
                Behavior Configuration
              </h2>

              <div className="bg-card border border-border rounded-lg p-4">
                <label htmlFor="assertiveness" className="block font-heading text-h3 text-text-primary mb-1">
                  Global Assertiveness Dial
                </label>
                <p className="font-body text-caption text-text-secondary mb-1">
                  Shifts all AI participants toward cooperation (1) or competition (10). Default: 5 (balanced).
                </p>
                <p className="font-body text-caption text-warning/80 mb-4 italic">
                  Applied at initialization. Change requires Shutdown → Re-initialize.
                </p>

                <div className="flex items-center gap-4">
                  <span className="font-body text-caption text-text-secondary w-24">Cooperative</span>
                  <input
                    id="assertiveness"
                    type="range"
                    min="1"
                    max="10"
                    value={assertiveness}
                    onChange={(e) => handleChange('assertiveness', e.target.value)}
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

            {/* ---- Stateless API Settings (immediate) ---- */}
            <section className="mb-10">
              <h2 className="font-heading text-h2 text-text-primary mb-2">
                Stateless API Settings
              </h2>
              <p className="font-body text-body-sm text-text-secondary mb-6">
                These settings apply to one-shot LLM calls (intelligence reports, chat, Navigator). Changes take effect <strong>immediately</strong>.
              </p>

              <div className="space-y-4">
                {STATELESS_SETTINGS.map(renderModelField)}
              </div>
            </section>

            {/* ---- Save ---- */}
            <div className="flex items-center gap-4">
              <button
                onClick={handleSaveAll}
                disabled={saving !== null}
                className="bg-action text-white font-body text-body-sm font-medium py-2 px-6 rounded hover:opacity-90 transition-opacity disabled:opacity-50"
              >
                {saving ? 'Saving...' : 'Save All Settings'}
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
