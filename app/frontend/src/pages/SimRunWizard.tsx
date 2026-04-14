/**
 * SimRun Creation / Edit Wizard — 5-step flow for setting up a simulation run.
 *
 * Routes:
 *   /sim/create   — new SimRun
 *   /sim/:id/edit — edit existing SimRun
 *
 * Steps: Template > Configure > Countries & Roles > Schedule > Review & Create
 */

import { useState, useEffect, useMemo, useCallback } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Header } from '@/components/Header'
import { useAuth } from '@/contexts/AuthContext'
import {
  getTemplates,
  getTemplate,
  getSimRun,
  createSimRun,
  updateSimRun,
  getSimRunRoles,
  type SimTemplate,
  type SimRun,
  type SimRunRole,
} from '@/lib/queries'
import { supabase } from '@/lib/supabase'

/* -------------------------------------------------------------------------- */
/*  Constants                                                                  */
/* -------------------------------------------------------------------------- */

const STEP_LABELS = [
  'Select Template',
  'Configure',
  'Countries & Roles',
  'Schedule',
  'Review & Create',
] as const

type StepIndex = 0 | 1 | 2 | 3 | 4

/** Default schedule when template has none. */
const FALLBACK_SCHEDULE: Record<string, number> = {
  default_rounds: 6,
  round_1_duration_min: 80,
  subsequent_round_duration_min: 60,
  break_duration_min: 15,
  introduction_duration_min: 30,
  reflection_duration_min: 20,
  debriefing_duration_min: 30,
}

/** The canonical default sim run that holds template reference data. */
const DEFAULT_SIM_RUN_ID = '00000000-0000-0000-0000-000000000001'

/** Represents a single role in the wizard's local state. */

interface WizardRole {
  id: string
  character_name: string
  country_id: string
  title: string
  is_head_of_state: boolean
  is_military_chief: boolean
  is_ai_operated: boolean
  is_economy_officer: boolean
  expansion_role: boolean
  powers: string[]
  active: boolean
}

/** Key event entry — structured schema matching template data. */
interface KeyEventParticipant {
  role_id: string
  country_code: string
  character_name: string
}

interface KeyEvent {
  type: string
  subtype?: string
  name: string
  round: number
  country_code?: string
  organization?: string
  participants?: KeyEventParticipant[]
  nominations_round?: number
  note?: string
}

/* -------------------------------------------------------------------------- */
/*  Main Component                                                             */
/* -------------------------------------------------------------------------- */

export function SimRunWizard() {
  const navigate = useNavigate()
  const { id: editId } = useParams<{ id: string }>()
  const { profile } = useAuth()
  const isEdit = Boolean(editId)

  /* ---- Wizard state ---- */
  const [step, setStep] = useState<StepIndex>(0)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  /* Step 1 — templates */
  const [templates, setTemplates] = useState<SimTemplate[]>([])
  const [templatesLoading, setTemplatesLoading] = useState(true)
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(null)
  const [selectedTemplate, setSelectedTemplate] = useState<SimTemplate | null>(null)

  /* Step 2 — configure */
  const [runName, setRunName] = useState('')
  const [runDescription, setRunDescription] = useState('')
  const [logoFile, setLogoFile] = useState<File | null>(null)
  const [logoPreview, setLogoPreview] = useState<string | null>(null)
  const [existingLogoUrl, setExistingLogoUrl] = useState<string | null>(null)

  /* Step 3 — roles */
  const [roles, setRoles] = useState<WizardRole[]>([])
  const [rolesLoading, setRolesLoading] = useState(false)
  const [rolesMessage, setRolesMessage] = useState<string | null>(null)

  /* Step 4 — schedule */
  const [schedule, setSchedule] = useState<Record<string, number>>(FALLBACK_SCHEDULE)
  const [maxRounds, setMaxRounds] = useState(6)
  const [keyEvents, setKeyEvents] = useState<KeyEvent[]>([])

  /* ---- Data loading ---- */

  useEffect(() => {
    const load = async () => {
      try {
        const tpls = await getTemplates()
        setTemplates(tpls)
      } catch (e) {
        console.error('Failed to load templates:', e)
      } finally {
        setTemplatesLoading(false)
      }
    }
    load()
  }, [])

  /** When editing, load existing SimRun and pre-populate all fields. */
  useEffect(() => {
    if (!editId) return
    const loadExisting = async () => {
      try {
        const run = await getSimRun(editId)
        if (!run) {
          setError('SimRun not found.')
          return
        }
        setRunName(run.name)
        setRunDescription(run.description ?? '')
        setExistingLogoUrl(run.logo_url)
        setLogoPreview(run.logo_url)
        setSchedule(run.schedule && Object.keys(run.schedule).length > 0 ? run.schedule : FALLBACK_SCHEDULE)
        setMaxRounds(run.max_rounds)
        setKeyEvents(
          Array.isArray(run.key_events)
            ? (run.key_events as KeyEvent[])
            : []
        )
        if (run.template_id) {
          setSelectedTemplateId(run.template_id)
          const tpl = await getTemplate(run.template_id)
          setSelectedTemplate(tpl)
        }
        // Load roles
        const existingRoles = await getSimRunRoles(editId)
        if (existingRoles.length > 0) {
          setRoles(
            existingRoles.map((r) => ({
              id: r.id,
              character_name: r.character_name,
              country_id: r.country_id,
              title: r.title,
              is_head_of_state: r.is_head_of_state,
              is_military_chief: r.is_military_chief,
              is_ai_operated: r.is_ai_operated,
              is_economy_officer: r.is_economy_officer ?? false,
              expansion_role: r.expansion_role ?? false,
              powers: r.powers ?? [],
              active: r.status !== 'inactive',
            }))
          )
        }
        // Jump to step 1 (Configure) since template is already selected
        setStep(1)
      } catch (e) {
        console.error('Failed to load SimRun for editing:', e)
        setError('Failed to load simulation data.')
      }
    }
    loadExisting()
  }, [editId])

  /** When a template is selected (new creation), load its defaults. */
  useEffect(() => {
    if (!selectedTemplateId || isEdit) return
    const loadTemplate = async () => {
      const tpl = await getTemplate(selectedTemplateId)
      setSelectedTemplate(tpl)
      if (tpl) {
        // Pre-fill schedule from template defaults
        if (tpl.schedule_defaults && Object.keys(tpl.schedule_defaults).length > 0) {
          setSchedule(tpl.schedule_defaults)
          if (tpl.schedule_defaults.default_rounds) {
            setMaxRounds(tpl.schedule_defaults.default_rounds)
          }
        }
        // Pre-fill key events
        if (Array.isArray(tpl.key_events_defaults) && tpl.key_events_defaults.length > 0) {
          setKeyEvents(tpl.key_events_defaults as KeyEvent[])
        }
        // Try to load roles from the first sim_run using this template
        await loadRolesFromTemplate(tpl.id)
      }
    }
    loadTemplate()
  }, [selectedTemplateId, isEdit])

  /** Load roles from the canonical default sim run (template reference data). */
  const loadRolesFromTemplate = async (_templateId: string) => {
    setRolesLoading(true)
    setRolesMessage(null)
    try {
      const sourceRoles = await getSimRunRoles(DEFAULT_SIM_RUN_ID)
      if (sourceRoles.length === 0) {
        setRoles([])
        setRolesMessage('No roles found in the template reference data.')
      } else {
        setRoles(
          sourceRoles.map((r) => ({
            id: r.id,
            character_name: r.character_name,
            country_id: r.country_id,
            title: r.title,
            is_head_of_state: r.is_head_of_state,
            is_military_chief: r.is_military_chief,
            is_ai_operated: r.is_ai_operated,
            is_economy_officer: r.is_economy_officer ?? false,
            expansion_role: r.expansion_role ?? false,
            powers: r.powers ?? [],
            active: true,
          }))
        )
      }
    } catch (e) {
      console.error('Failed to load template roles:', e)
      setRolesMessage('Could not load roles. They can be configured after creation.')
    } finally {
      setRolesLoading(false)
    }
  }

  /* ---- Derived data ---- */

  const rolesByCountry = useMemo(() => {
    const grouped: Record<string, WizardRole[]> = {}
    for (const role of roles) {
      if (!grouped[role.country_id]) grouped[role.country_id] = []
      grouped[role.country_id].push(role)
    }
    return grouped
  }, [roles])

  const roleSummary = useMemo(() => {
    const active = roles.filter((r) => r.active)
    const human = active.filter((r) => !r.is_ai_operated).length
    const ai = active.filter((r) => r.is_ai_operated).length
    const countries = new Set(active.map((r) => r.country_id)).size
    return { countries, total: active.length, human, ai }
  }, [roles])

  const scheduleTotalMinutes = useMemo(() => {
    const r1 = schedule.round_1_duration_min ?? 80
    const rN = schedule.subsequent_round_duration_min ?? 60
    const breakMin = schedule.break_duration_min ?? 15
    const introMin = schedule.introduction_duration_min ?? 30
    const reflectionMin = schedule.reflection_duration_min ?? 20
    const debriefMin = schedule.debriefing_duration_min ?? 30
    const netPlay = r1 + rN * Math.max(0, maxRounds - 1)
    const totalBreaks = breakMin * Math.max(0, maxRounds - 1)
    return {
      netPlay,
      totalBreaks,
      totalEvent: introMin + netPlay + totalBreaks + reflectionMin + debriefMin,
    }
  }, [schedule, maxRounds])

  /* ---- Validation ---- */

  const canProceed = useCallback((): boolean => {
    switch (step) {
      case 0:
        return selectedTemplateId !== null
      case 1:
        return runName.trim().length > 0
      case 2:
        return true // roles are optional at creation time
      case 3:
        return maxRounds > 0
      case 4:
        return true
      default:
        return false
    }
  }, [step, selectedTemplateId, runName, maxRounds])

  /* ---- Logo upload helper ---- */

  const uploadLogo = async (): Promise<string | null> => {
    if (!logoFile) return existingLogoUrl
    const ext = logoFile.name.split('.').pop() ?? 'png'
    const path = `sim-logos/${Date.now()}-${Math.random().toString(36).slice(2)}.${ext}`
    const { error: uploadError } = await supabase.storage
      .from('assets')
      .upload(path, logoFile, { contentType: logoFile.type })

    if (uploadError) {
      console.error('Logo upload failed:', uploadError)
      return existingLogoUrl
    }
    const { data: urlData } = supabase.storage.from('assets').getPublicUrl(path)
    return urlData.publicUrl
  }

  /* ---- Submit ---- */

  const handleSubmit = async () => {
    if (!profile) {
      setError('Not authenticated. Please sign in again.')
      return
    }
    setSubmitting(true)
    setError(null)
    try {
      let logoUrl: string | null = null
      if (logoFile) {
        logoUrl = await uploadLogo()
      } else {
        logoUrl = existingLogoUrl
      }

      if (isEdit && editId) {
        console.log('Updating sim run:', editId)
        await updateSimRun(editId, {
          name: runName.trim(),
          description: runDescription.trim() || null,
          logo_url: logoUrl,
          schedule,
          key_events: keyEvents as unknown[],
          max_rounds: maxRounds,
          human_participants: roleSummary.human,
          ai_participants: roleSummary.ai,
        } as Partial<SimRun>)
        console.log('Update successful')
        navigate('/dashboard')
      } else {
        if (!selectedTemplateId) {
          setError('No template selected.')
          setSubmitting(false)
          return
        }
        console.log('Creating sim run...')
        const newRun = await createSimRun({
          name: runName.trim(),
          template_id: selectedTemplateId,
          facilitator_id: profile.id,
          schedule,
          key_events: keyEvents as unknown[],
          max_rounds: maxRounds,
          human_participants: roleSummary.human,
          ai_participants: roleSummary.ai,
          logo_url: logoUrl ?? undefined,
          description: runDescription.trim() || undefined,
        })
        console.log('Created sim run:', newRun.id)
        navigate('/dashboard')
      }
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'An unexpected error occurred.'
      setError(msg)
      console.error('Submit failed:', e)
      setSubmitting(false)
    }
  }

  /* ---- Role helpers ---- */

  const toggleRole = (roleId: string) => {
    setRoles((prev) =>
      prev.map((r) => (r.id === roleId ? { ...r, active: !r.active } : r))
    )
  }

  const toggleRoleAi = (roleId: string, isAi: boolean) => {
    setRoles((prev) =>
      prev.map((r) => (r.id === roleId ? { ...r, is_ai_operated: isAi } : r))
    )
  }

  const toggleCountryAll = (countryId: string, active: boolean) => {
    setRoles((prev) =>
      prev.map((r) =>
        r.country_id === countryId ? { ...r, active } : r
      )
    )
  }

  const setCountryAllAi = (countryId: string, isAi: boolean) => {
    setRoles((prev) =>
      prev.map((r) =>
        r.country_id === countryId ? { ...r, is_ai_operated: isAi } : r
      )
    )
  }

  /* ---- Schedule helpers ---- */

  const updateScheduleField = (key: string, value: number) => {
    setSchedule((prev) => ({ ...prev, [key]: value }))
  }

  const updateKeyEventRound = (index: number, round: number) => {
    setKeyEvents((prev) =>
      prev.map((ev, i) =>
        i === index ? { ...ev, round } : ev
      )
    )
  }

  /* ---- Logo file handler ---- */

  const handleLogoSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setLogoFile(file)
    const reader = new FileReader()
    reader.onloadend = () => setLogoPreview(reader.result as string)
    reader.readAsDataURL(file)
  }

  const removeLogo = () => {
    setLogoFile(null)
    setLogoPreview(null)
    setExistingLogoUrl(null)
  }

  /* ---- Navigation ---- */

  const goNext = () => {
    if (canProceed() && step < 4) setStep((step + 1) as StepIndex)
  }

  const goPrev = () => {
    if (step > 0) setStep((step - 1) as StepIndex)
  }

  /* ---- Render ---- */

  return (
    <div className="min-h-screen bg-base">
      <Header subtitle={isEdit ? 'Edit Simulation' : 'Create Simulation'} />

      <main className="max-w-4xl mx-auto px-6 py-8">
        {/* Step indicator */}
        <StepIndicator currentStep={step} isEdit={isEdit} onStepClick={(s) => {
          // In edit mode: free navigation to any step
          // In create mode: only back to completed steps
          if (isEdit || s < step) setStep(s)
        }} />

        {/* Error banner */}
        {error && (
          <div className="bg-danger/10 border border-danger/30 rounded-lg p-4 mb-6">
            <p className="font-body text-body-sm text-danger">{error}</p>
          </div>
        )}

        {/* Step content */}
        <div className="bg-card border border-border rounded-lg p-6 mb-6">
          {step === 0 && (
            <StepSelectTemplate
              templates={templates}
              loading={templatesLoading}
              selectedId={selectedTemplateId}
              onSelect={(id) => setSelectedTemplateId(id)}
            />
          )}
          {step === 1 && (
            <StepConfigure
              name={runName}
              description={runDescription}
              logoPreview={logoPreview}
              onNameChange={setRunName}
              onDescriptionChange={setRunDescription}
              onLogoSelect={handleLogoSelect}
              onLogoRemove={removeLogo}
              templateName={selectedTemplate?.name ?? ''}
            />
          )}
          {step === 2 && (
            <StepCountriesRoles
              rolesByCountry={rolesByCountry}
              loading={rolesLoading}
              message={rolesMessage}
              summary={roleSummary}
              onToggleRole={toggleRole}
              onToggleRoleAi={toggleRoleAi}
              onToggleCountryAll={toggleCountryAll}
              onSetCountryAllAi={setCountryAllAi}
            />
          )}
          {step === 3 && (
            <StepSchedule
              schedule={schedule}
              maxRounds={maxRounds}
              keyEvents={keyEvents}
              totals={scheduleTotalMinutes}
              onUpdateSchedule={updateScheduleField}
              onMaxRoundsChange={setMaxRounds}
              onUpdateKeyEventRound={updateKeyEventRound}
            />
          )}
          {step === 4 && (
            <StepReview
              isEdit={isEdit}
              templateName={selectedTemplate?.name ?? 'Unknown'}
              runName={runName}
              runDescription={runDescription}
              logoPreview={logoPreview}
              roleSummary={roleSummary}
              schedule={schedule}
              maxRounds={maxRounds}
              keyEvents={keyEvents}
              totals={scheduleTotalMinutes}
            />
          )}
        </div>

        {/* Navigation buttons */}
        <div className="flex items-center justify-between">
          <button
            onClick={() => step === 0 ? navigate('/dashboard') : goPrev()}
            className="font-body text-body-sm text-text-secondary hover:text-text-primary transition-colors px-4 py-2"
          >
            {step === 0 ? 'Cancel' : 'Previous'}
          </button>

          {step < 4 ? (
            <button
              onClick={goNext}
              disabled={!canProceed()}
              className={`font-body text-body-sm font-medium py-2 px-6 rounded transition-opacity ${
                canProceed()
                  ? 'bg-action text-white hover:opacity-90 cursor-pointer'
                  : 'bg-action/40 text-white/60 cursor-not-allowed'
              }`}
            >
              Next
            </button>
          ) : (
            <button
              onClick={handleSubmit}
              disabled={submitting}
              className={`font-body text-body-sm font-medium py-2 px-6 rounded transition-opacity ${
                submitting
                  ? 'bg-action/40 text-white/60 cursor-not-allowed'
                  : 'bg-action text-white hover:opacity-90 cursor-pointer'
              }`}
            >
              {submitting
                ? 'Saving...'
                : isEdit
                  ? 'Save Changes'
                  : 'Create Simulation'}
            </button>
          )}
        </div>
      </main>
    </div>
  )
}

/* ========================================================================== */
/*  Step Indicator                                                             */
/* ========================================================================== */

function StepIndicator({
  currentStep,
  isEdit,
  onStepClick,
}: {
  currentStep: StepIndex
  isEdit: boolean
  onStepClick: (step: StepIndex) => void
}) {
  return (
    <nav className="flex items-center justify-between mb-8">
      {STEP_LABELS.map((label, i) => {
        const isActive = i === currentStep
        const isCompleted = i < currentStep
        const isClickable = isEdit || i <= currentStep
        const stepNum = i as StepIndex
        return (
          <button
            key={label}
            onClick={() => onStepClick(stepNum)}
            disabled={!isClickable}
            className={`flex items-center gap-2 group ${
              isClickable ? 'cursor-pointer' : 'cursor-not-allowed'
            }`}
          >
            <span
              className={`flex items-center justify-center w-8 h-8 rounded-full font-data text-data font-medium transition-colors ${
                isActive
                  ? 'bg-action text-white'
                  : isCompleted
                    ? 'bg-action/20 text-action'
                    : 'bg-border text-text-secondary'
              }`}
            >
              {isCompleted ? '\u2713' : i + 1}
            </span>
            <span
              className={`font-body text-caption hidden sm:inline transition-colors ${
                isActive
                  ? 'text-text-primary font-medium'
                  : isCompleted
                    ? 'text-action'
                    : 'text-text-secondary'
              }`}
            >
              {label}
            </span>
            {i < STEP_LABELS.length - 1 && (
              <span
                className={`hidden md:block w-8 h-px mx-1 ${
                  isCompleted ? 'bg-action/40' : 'bg-border'
                }`}
              />
            )}
          </button>
        )
      })}
    </nav>
  )
}

/* ========================================================================== */
/*  Step 1 — Select Template                                                   */
/* ========================================================================== */

function StepSelectTemplate({
  templates,
  loading,
  selectedId,
  onSelect,
}: {
  templates: SimTemplate[]
  loading: boolean
  selectedId: string | null
  onSelect: (id: string) => void
}) {
  return (
    <div>
      <h2 className="font-heading text-h2 text-text-primary mb-2">
        Select Template
      </h2>
      <p className="font-body text-body-sm text-text-secondary mb-6">
        Choose the scenario template that will define the world, countries, and rules for this simulation.
      </p>

      {loading ? (
        <p className="font-body text-body-sm text-text-secondary">
          Loading templates...
        </p>
      ) : templates.length === 0 ? (
        <div className="border border-border rounded-lg p-8 text-center">
          <p className="font-body text-body text-text-secondary">
            No templates available. Create a template first.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {templates.map((tpl) => (
            <button
              key={tpl.id}
              onClick={() => onSelect(tpl.id)}
              className={`w-full text-left border rounded-lg p-4 transition-colors ${
                selectedId === tpl.id
                  ? 'border-action bg-action/5'
                  : 'border-border hover:border-action/30'
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <h3 className="font-heading text-h3 text-text-primary">
                  {tpl.name}
                </h3>
                <div className="flex items-center gap-2">
                  <span className="font-data text-data text-text-secondary">
                    v{tpl.version}
                  </span>
                  <span
                    className={`font-body text-caption font-medium px-2 py-0.5 rounded ${
                      tpl.status === 'active'
                        ? 'bg-success/10 text-success'
                        : 'bg-warning/10 text-warning'
                    }`}
                  >
                    {tpl.status}
                  </span>
                </div>
              </div>
              <p className="font-body text-caption text-text-secondary">
                {tpl.description ?? 'No description'}
              </p>
              <p className="font-body text-caption text-text-secondary mt-1">
                Code: <span className="font-data text-data">{tpl.code}</span>
              </p>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

/* ========================================================================== */
/*  Step 2 — Configure                                                         */
/* ========================================================================== */

function StepConfigure({
  name,
  description,
  logoPreview,
  onNameChange,
  onDescriptionChange,
  onLogoSelect,
  onLogoRemove,
  templateName,
}: {
  name: string
  description: string
  logoPreview: string | null
  onNameChange: (v: string) => void
  onDescriptionChange: (v: string) => void
  onLogoSelect: (e: React.ChangeEvent<HTMLInputElement>) => void
  onLogoRemove: () => void
  templateName: string
}) {
  return (
    <div>
      <h2 className="font-heading text-h2 text-text-primary mb-2">
        Configure Simulation
      </h2>
      <p className="font-body text-body-sm text-text-secondary mb-6">
        Template: <span className="text-text-primary font-medium">{templateName}</span>
      </p>

      <div className="space-y-5">
        {/* Name */}
        <div>
          <label className="block font-body text-body-sm text-text-primary mb-1">
            Simulation Name <span className="text-danger">*</span>
          </label>
          <input
            type="text"
            value={name}
            onChange={(e) => onNameChange(e.target.value)}
            placeholder="e.g. Spring 2026 Crisis Exercise"
            className="w-full bg-base border border-border rounded px-3 py-2 font-body text-body-sm text-text-primary placeholder:text-text-secondary/50 focus:outline-none focus:border-action transition-colors"
          />
        </div>

        {/* Description */}
        <div>
          <label className="block font-body text-body-sm text-text-primary mb-1">
            Description <span className="text-text-secondary">(optional)</span>
          </label>
          <textarea
            value={description}
            onChange={(e) => onDescriptionChange(e.target.value)}
            placeholder="Brief description of this simulation run..."
            rows={3}
            className="w-full bg-base border border-border rounded px-3 py-2 font-body text-body-sm text-text-primary placeholder:text-text-secondary/50 focus:outline-none focus:border-action transition-colors resize-none"
          />
        </div>

        {/* Logo */}
        <div>
          <label className="block font-body text-body-sm text-text-primary mb-1">
            Logo <span className="text-text-secondary">(optional)</span>
          </label>
          <div className="flex items-center gap-4">
            {logoPreview ? (
              <div className="relative">
                <img
                  src={logoPreview}
                  alt="Logo preview"
                  className="w-16 h-16 rounded-lg object-cover border border-border"
                />
                <button
                  onClick={onLogoRemove}
                  className="absolute -top-2 -right-2 w-5 h-5 bg-danger text-white rounded-full flex items-center justify-center font-body text-caption leading-none hover:opacity-80"
                  title="Remove logo"
                >
                  x
                </button>
              </div>
            ) : (
              <label className="w-16 h-16 rounded-lg border border-dashed border-border flex items-center justify-center cursor-pointer hover:border-action/40 transition-colors">
                <span className="font-body text-caption text-text-secondary">+</span>
                <input
                  type="file"
                  accept="image/*"
                  onChange={onLogoSelect}
                  className="hidden"
                />
              </label>
            )}
            <p className="font-body text-caption text-text-secondary">
              Square image recommended. PNG or JPG, max 2 MB.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

/* ========================================================================== */
/*  Step 3 — Countries & Roles                                                 */
/* ========================================================================== */

function StepCountriesRoles({
  rolesByCountry,
  loading,
  message,
  summary,
  onToggleRole,
  onToggleRoleAi,
  onToggleCountryAll,
  onSetCountryAllAi,
}: {
  rolesByCountry: Record<string, WizardRole[]>
  loading: boolean
  message: string | null
  summary: { countries: number; total: number; human: number; ai: number }
  onToggleRole: (id: string) => void
  onToggleRoleAi: (id: string, isAi: boolean) => void
  onToggleCountryAll: (countryId: string, active: boolean) => void
  onSetCountryAllAi: (countryId: string, isAi: boolean) => void
}) {
  // Custom sort: large teams → EU → mid-size → solo (alphabetical)
  const COUNTRY_ORDER: string[] = [
    // Large teams
    'columbia', 'cathay',
    // Ereb Union
    'gallia', 'teutonia', 'ponte', 'freeland', 'albion',
    // Mid-size teams
    'sarmatia', 'ruthenia', 'persia',
    // Solo countries (alphabetical)
    'bharata', 'caribe', 'choson', 'formosa', 'hanguk',
    'levantia', 'mirage', 'phrygia', 'solaria', 'yamato',
  ]
  const countries = Object.keys(rolesByCountry).sort((a, b) => {
    const ia = COUNTRY_ORDER.indexOf(a)
    const ib = COUNTRY_ORDER.indexOf(b)
    // If both in order list, sort by position; unknown countries go to end alphabetically
    if (ia >= 0 && ib >= 0) return ia - ib
    if (ia >= 0) return -1
    if (ib >= 0) return 1
    return a.localeCompare(b)
  })

  return (
    <div>
      <h2 className="font-heading text-h2 text-text-primary mb-2">
        Countries & Roles
      </h2>
      <p className="font-body text-body-sm text-text-secondary mb-6">
        Toggle roles on/off and set each as Human or AI operated.
      </p>

      {loading ? (
        <p className="font-body text-body-sm text-text-secondary">
          Loading roles...
        </p>
      ) : message && countries.length === 0 ? (
        <div className="border border-border rounded-lg p-6 text-center">
          <p className="font-body text-body-sm text-text-secondary">
            {message}
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {countries.map((countryId) => {
            const countryRoles = rolesByCountry[countryId]
            const allActive = countryRoles.every((r) => r.active)
            const allAi = countryRoles.every((r) => r.is_ai_operated)

            return (
              <div
                key={countryId}
                className="border border-border rounded-lg overflow-hidden"
              >
                {/* Country header */}
                <div className="bg-base px-4 py-3 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <button
                      onClick={() => onToggleCountryAll(countryId, !allActive)}
                      className={`w-5 h-5 rounded border flex items-center justify-center transition-colors ${
                        allActive
                          ? 'bg-action border-action text-white'
                          : 'border-border hover:border-action/40'
                      }`}
                    >
                      {allActive && (
                        <span className="text-xs leading-none">{'\u2713'}</span>
                      )}
                    </button>
                    <h3 className="font-heading text-h3 text-text-primary">
                      {countryId.charAt(0).toUpperCase() + countryId.slice(1)}
                    </h3>
                    <span className="font-data text-data text-text-secondary">
                      {countryRoles.filter((r) => r.active).length}/{countryRoles.length} roles
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="font-body text-caption text-text-secondary mr-1">
                      All:
                    </span>
                    <button
                      onClick={() => onSetCountryAllAi(countryId, false)}
                      className={`font-body text-caption px-2 py-0.5 rounded transition-colors ${
                        !allAi
                          ? 'bg-action/10 text-action font-medium'
                          : 'text-text-secondary hover:text-text-primary'
                      }`}
                    >
                      Human
                    </button>
                    <button
                      onClick={() => onSetCountryAllAi(countryId, true)}
                      className={`font-body text-caption px-2 py-0.5 rounded transition-colors ${
                        allAi
                          ? 'bg-accent/10 text-accent font-medium'
                          : 'text-text-secondary hover:text-text-primary'
                      }`}
                    >
                      AI
                    </button>
                  </div>
                </div>

                {/* Role rows */}
                <div className="divide-y divide-border">
                  {countryRoles.map((role) => (
                    <div
                      key={role.id}
                      className={`px-4 py-2.5 flex items-center justify-between transition-opacity ${
                        role.active ? '' : 'opacity-40'
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <button
                          onClick={() => onToggleRole(role.id)}
                          className={`w-4 h-4 rounded border flex items-center justify-center transition-colors ${
                            role.active
                              ? 'bg-action border-action text-white'
                              : 'border-border hover:border-action/40'
                          }`}
                        >
                          {role.active && (
                            <span className="text-[10px] leading-none">{'\u2713'}</span>
                          )}
                        </button>
                        <div>
                          <span className="font-body text-body-sm text-text-primary">
                            {role.character_name}
                          </span>
                          <span className="font-body text-caption text-text-secondary ml-2">
                            {role.title}
                          </span>
                          {role.is_head_of_state && (
                            <span className="font-body text-caption font-medium bg-warning/10 text-warning px-1.5 py-0.5 rounded ml-2">
                              HoS
                            </span>
                          )}
                          {role.is_military_chief && !role.is_head_of_state && (
                            <span className="font-body text-caption font-medium bg-danger/10 text-danger px-1.5 py-0.5 rounded ml-2">
                              Military
                            </span>
                          )}
                          {role.is_economy_officer && !role.is_head_of_state && (
                            <span className="font-body text-caption font-medium bg-accent/10 text-accent px-1.5 py-0.5 rounded ml-2">
                              Economy
                            </span>
                          )}
                          {role.expansion_role && (
                            <span className="font-body text-caption font-medium text-text-secondary bg-border/50 px-1.5 py-0.5 rounded ml-2">
                              optional
                            </span>
                          )}
                        </div>
                      </div>

                      {role.active && (
                        <div className="flex items-center gap-1">
                          <button
                            onClick={() => onToggleRoleAi(role.id, false)}
                            className={`font-body text-caption px-2 py-0.5 rounded transition-colors ${
                              !role.is_ai_operated
                                ? 'bg-action/10 text-action font-medium'
                                : 'text-text-secondary hover:text-text-primary'
                            }`}
                          >
                            Human
                          </button>
                          <button
                            onClick={() => onToggleRoleAi(role.id, true)}
                            className={`font-body text-caption px-2 py-0.5 rounded transition-colors ${
                              role.is_ai_operated
                                ? 'bg-accent/10 text-accent font-medium'
                                : 'text-text-secondary hover:text-text-primary'
                            }`}
                          >
                            AI
                          </button>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )
          })}

          {/* Summary bar */}
          {countries.length > 0 && (
            <div className="bg-base border border-border rounded-lg px-4 py-3 flex items-center justify-between">
              <span className="font-body text-body-sm text-text-primary font-medium">
                Summary
              </span>
              <span className="font-data text-data text-text-secondary">
                {summary.countries} countries, {summary.total} roles ({summary.human} human, {summary.ai} AI)
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

/* ========================================================================== */
/*  Step 4 — Schedule                                                          */
/* ========================================================================== */

/** Human-friendly label for schedule keys. */
const SCHEDULE_LABELS: Record<string, string> = {
  default_rounds: 'Default Rounds',
  round_1_duration_min: 'Round 1 Duration (min)',
  subsequent_round_duration_min: 'Subsequent Rounds Duration (min)',
  break_duration_min: 'Break Between Rounds (min)',
  introduction_duration_min: 'Introduction Duration (min)',
  reflection_duration_min: 'Reflection Duration (min)',
  debriefing_duration_min: 'Debriefing Duration (min)',
}

function StepSchedule({
  schedule,
  maxRounds,
  keyEvents,
  totals,
  onUpdateSchedule,
  onMaxRoundsChange,
  onUpdateKeyEventRound,
}: {
  schedule: Record<string, number>
  maxRounds: number
  keyEvents: KeyEvent[]
  totals: { netPlay: number; totalBreaks: number; totalEvent: number }
  onUpdateSchedule: (key: string, value: number) => void
  onMaxRoundsChange: (v: number) => void
  onUpdateKeyEventRound: (i: number, round: number) => void
}) {
  return (
    <div>
      <h2 className="font-heading text-h2 text-text-primary mb-2">
        Schedule
      </h2>
      <p className="font-body text-body-sm text-text-secondary mb-6">
        Configure round durations, breaks, and key events.
      </p>

      <div className="space-y-6">
        {/* Max rounds */}
        <div>
          <label className="block font-body text-body-sm text-text-primary mb-1">
            Number of Rounds
          </label>
          <input
            type="number"
            min={1}
            max={20}
            value={maxRounds}
            onChange={(e) => onMaxRoundsChange(Math.max(1, parseInt(e.target.value) || 1))}
            className="w-24 bg-base border border-border rounded px-3 py-2 font-data text-data text-text-primary focus:outline-none focus:border-action transition-colors"
          />
        </div>

        {/* Duration fields */}
        <div>
          <h3 className="font-heading text-h3 text-text-primary mb-3">
            Durations
          </h3>
          <div className="grid grid-cols-2 gap-4">
            {Object.entries(schedule)
              .filter(([key]) => key !== 'default_rounds')
              .map(([key, value]) => (
              <div key={key}>
                <label className="block font-body text-caption text-text-secondary mb-1">
                  {SCHEDULE_LABELS[key] ?? key.replace(/_/g, ' ')}
                </label>
                <input
                  type="number"
                  min={0}
                  value={value}
                  onChange={(e) =>
                    onUpdateSchedule(key, Math.max(0, parseInt(e.target.value) || 0))
                  }
                  className="w-full bg-base border border-border rounded px-3 py-2 font-data text-data text-text-primary focus:outline-none focus:border-action transition-colors"
                />
              </div>
            ))}
          </div>
        </div>

        {/* Calculated totals */}
        <div className="bg-base border border-border rounded-lg p-4">
          <h3 className="font-heading text-h3 text-text-primary mb-2">
            Calculated Totals
          </h3>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <p className="font-body text-caption text-text-secondary">Net Play Time</p>
              <p className="font-data text-data text-text-primary">
                {totals.netPlay} min ({(totals.netPlay / 60).toFixed(1)} hrs)
              </p>
            </div>
            <div>
              <p className="font-body text-caption text-text-secondary">Total Breaks</p>
              <p className="font-data text-data text-text-primary">
                {totals.totalBreaks} min
              </p>
            </div>
            <div>
              <p className="font-body text-caption text-text-secondary">Total Event Time</p>
              <p className="font-data text-data text-action font-medium">
                {totals.totalEvent} min ({(totals.totalEvent / 60).toFixed(1)} hrs)
              </p>
            </div>
          </div>
        </div>

        {/* Key events */}
        <div>
          <h3 className="font-heading text-h3 text-text-primary mb-3">
            Key Events
          </h3>

          {keyEvents.length === 0 ? (
            <p className="font-body text-caption text-text-secondary">
              No key events configured in template.
            </p>
          ) : (
            <div className="space-y-2">
              {keyEvents.map((ev, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between border border-border rounded px-4 py-2.5"
                >
                  <div className="flex-1">
                    <span className="font-body text-body-sm text-text-primary">
                      {ev.name}
                    </span>
                    {ev.type === 'election' && ev.nominations_round && (
                      <span className="font-body text-caption text-text-secondary ml-2">
                        (nominations R{ev.nominations_round})
                      </span>
                    )}
                    {ev.participants && ev.participants.length > 0 && (
                      <span className="font-body text-caption text-text-secondary ml-2">
                        — {ev.participants.map((p) => p.character_name).join(', ')}
                      </span>
                    )}
                    {ev.note && (
                      <span className="font-body text-caption text-text-secondary/70 ml-1">
                        ({ev.note})
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <span
                      className={`font-body text-caption px-2 py-0.5 rounded ${
                        ev.type === 'election'
                          ? 'bg-warning/10 text-warning'
                          : 'bg-action/10 text-action'
                      }`}
                    >
                      {ev.type === 'election' ? 'Election' : 'Meeting'}
                    </span>
                    <label className="font-body text-caption text-text-secondary">
                      Round:
                    </label>
                    <input
                      type="number"
                      min={1}
                      max={maxRounds}
                      value={ev.round}
                      onChange={(e) =>
                        onUpdateKeyEventRound(i, Math.max(1, parseInt(e.target.value) || 1))
                      }
                      className="w-16 bg-base border border-border rounded px-2 py-2 font-data text-data text-text-primary focus:outline-none focus:border-action transition-colors"
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

/* ========================================================================== */
/*  Step 5 — Review & Create                                                   */
/* ========================================================================== */

function StepReview({
  isEdit,
  templateName,
  runName,
  runDescription,
  logoPreview,
  roleSummary,
  schedule,
  maxRounds,
  keyEvents,
  totals,
}: {
  isEdit: boolean
  templateName: string
  runName: string
  runDescription: string
  logoPreview: string | null
  roleSummary: { countries: number; total: number; human: number; ai: number }
  schedule: Record<string, number>
  maxRounds: number
  keyEvents: KeyEvent[]
  totals: { netPlay: number; totalBreaks: number; totalEvent: number }
}) {
  return (
    <div>
      <h2 className="font-heading text-h2 text-text-primary mb-2">
        {isEdit ? 'Review Changes' : 'Review & Create'}
      </h2>
      <p className="font-body text-body-sm text-text-secondary mb-6">
        Verify all settings before {isEdit ? 'saving' : 'creating the simulation'}.
      </p>

      <div className="space-y-6">
        {/* Template & Config */}
        <ReviewSection title="Configuration">
          <div className="grid grid-cols-2 gap-4">
            <ReviewField label="Template" value={templateName} />
            <ReviewField label="Name" value={runName} />
            <ReviewField
              label="Description"
              value={runDescription || '(none)'}
            />
            <div>
              <p className="font-body text-caption text-text-secondary mb-1">Logo</p>
              {logoPreview ? (
                <img
                  src={logoPreview}
                  alt="Logo"
                  className="w-10 h-10 rounded border border-border object-cover"
                />
              ) : (
                <p className="font-body text-body-sm text-text-secondary">(none)</p>
              )}
            </div>
          </div>
        </ReviewSection>

        {/* Roles */}
        <ReviewSection title="Countries & Roles">
          {roleSummary.total === 0 ? (
            <p className="font-body text-body-sm text-text-secondary">
              No roles configured. Roles will be created when the simulation initializes.
            </p>
          ) : (
            <div className="grid grid-cols-4 gap-4">
              <ReviewField
                label="Countries"
                value={String(roleSummary.countries)}
                mono
              />
              <ReviewField
                label="Total Roles"
                value={String(roleSummary.total)}
                mono
              />
              <ReviewField
                label="Human"
                value={String(roleSummary.human)}
                mono
              />
              <ReviewField
                label="AI"
                value={String(roleSummary.ai)}
                mono
              />
            </div>
          )}
        </ReviewSection>

        {/* Schedule */}
        <ReviewSection title="Schedule">
          <div className="grid grid-cols-2 gap-4 mb-4">
            <ReviewField label="Rounds" value={String(maxRounds)} mono />
            {Object.entries(schedule).map(([key, val]) => (
              <ReviewField
                key={key}
                label={SCHEDULE_LABELS[key] ?? key.replace(/_/g, ' ')}
                value={`${val} min`}
                mono
              />
            ))}
          </div>
          <div className="bg-base border border-border rounded p-3 grid grid-cols-3 gap-4">
            <div>
              <p className="font-body text-caption text-text-secondary">Net Play</p>
              <p className="font-data text-data text-text-primary">
                {totals.netPlay} min
              </p>
            </div>
            <div>
              <p className="font-body text-caption text-text-secondary">Breaks</p>
              <p className="font-data text-data text-text-primary">
                {totals.totalBreaks} min
              </p>
            </div>
            <div>
              <p className="font-body text-caption text-text-secondary">Total Event</p>
              <p className="font-data text-data text-action font-medium">
                {totals.totalEvent} min ({(totals.totalEvent / 60).toFixed(1)} hrs)
              </p>
            </div>
          </div>
        </ReviewSection>

        {/* Key Events */}
        {keyEvents.length > 0 && (
          <ReviewSection title="Key Events">
            <div className="space-y-1">
              {keyEvents.map((ev, i) => (
                <div key={i} className="flex items-center gap-3">
                  <span className="font-data text-data text-text-secondary w-16">
                    Round {ev.round}
                  </span>
                  <span className="font-body text-body-sm text-text-primary">
                    {ev.name || '(unnamed)'}
                  </span>
                </div>
              ))}
            </div>
          </ReviewSection>
        )}
      </div>
    </div>
  )
}

/* -------------------------------------------------------------------------- */
/*  Review helpers                                                             */
/* -------------------------------------------------------------------------- */

function ReviewSection({
  title,
  children,
}: {
  title: string
  children: React.ReactNode
}) {
  return (
    <div>
      <h3 className="font-heading text-h3 text-text-primary mb-3 pb-2 border-b border-border">
        {title}
      </h3>
      {children}
    </div>
  )
}

function ReviewField({
  label,
  value,
  mono,
}: {
  label: string
  value: string
  mono?: boolean
}) {
  return (
    <div>
      <p className="font-body text-caption text-text-secondary mb-0.5">{label}</p>
      <p
        className={`text-text-primary ${
          mono ? 'font-data text-data' : 'font-body text-body-sm'
        }`}
      >
        {value}
      </p>
    </div>
  )
}
