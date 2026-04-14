/**
 * TabSchedule — template schedule defaults editor.
 * Edits schedule_defaults and key_events_defaults JSONB on the sim_templates row.
 * Calculated totals use the same formula as SimRunWizard Step 4.
 */

import { useState, useEffect, useMemo, useCallback } from 'react'
import {
  getTemplate, updateTemplate,
  getTemplateOrganizations, getTemplateRoles, getTemplateCountries,
  type SimTemplate, type Organization, type Role, type Country,
} from '@/lib/queries'

/* -------------------------------------------------------------------------- */
/*  Props                                                                      */
/* -------------------------------------------------------------------------- */

interface TabScheduleProps {
  templateId: string
}

/* -------------------------------------------------------------------------- */
/*  Constants                                                                  */
/* -------------------------------------------------------------------------- */

/** Human-friendly labels for schedule keys. */
const SCHEDULE_LABELS: Record<string, string> = {
  default_rounds: 'Default Rounds',
  round_1_duration_min: 'Round 1 Duration (min)',
  subsequent_round_duration_min: 'Subsequent Rounds Duration (min)',
  break_duration_min: 'Break Between Rounds (min)',
  introduction_duration_min: 'Introduction Duration (min)',
  reflection_duration_min: 'Reflection Duration (min)',
  debriefing_duration_min: 'Debriefing Duration (min)',
}

/** Duration fields shown in the 2-column grid (excludes default_rounds). */
const DURATION_FIELDS = [
  'round_1_duration_min',
  'subsequent_round_duration_min',
  'break_duration_min',
  'introduction_duration_min',
  'reflection_duration_min',
  'debriefing_duration_min',
] as const

/** Fallback schedule when template has no defaults. */
const FALLBACK_SCHEDULE: Record<string, number> = {
  default_rounds: 6,
  round_1_duration_min: 80,
  subsequent_round_duration_min: 60,
  break_duration_min: 15,
  introduction_duration_min: 30,
  reflection_duration_min: 20,
  debriefing_duration_min: 30,
}

/** Capitalize first letter. */
function cap(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1)
}

/* -------------------------------------------------------------------------- */
/*  Key Event types                                                            */
/* -------------------------------------------------------------------------- */

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
/*  Component                                                                  */
/* -------------------------------------------------------------------------- */

export function TabSchedule({ templateId }: TabScheduleProps) {
  const [loading, setLoading] = useState(true)
  const [template, setTemplate] = useState<SimTemplate | null>(null)
  const [schedule, setSchedule] = useState<Record<string, number>>(FALLBACK_SCHEDULE)
  const [keyEvents, setKeyEvents] = useState<KeyEvent[]>([])
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showAddEvent, setShowAddEvent] = useState(false)
  const [organizations, setOrganizations] = useState<Organization[]>([])
  const [roles, setRoles] = useState<Role[]>([])
  const [countries, setCountries] = useState<Country[]>([])

  /* ---- Load template data ---- */

  useEffect(() => {
    let cancelled = false
    const load = async () => {
      setLoading(true)
      try {
        const [tpl, orgs, rls, ctrs] = await Promise.all([
          getTemplate(templateId),
          getTemplateOrganizations(),
          getTemplateRoles(),
          getTemplateCountries(),
        ])
        if (cancelled) return
        setOrganizations(orgs)
        setRoles(rls)
        setCountries(ctrs)
        setTemplate(tpl)
        if (tpl) {
          const sched =
            tpl.schedule_defaults && Object.keys(tpl.schedule_defaults).length > 0
              ? tpl.schedule_defaults
              : FALLBACK_SCHEDULE
          setSchedule(sched)
          setKeyEvents(
            Array.isArray(tpl.key_events_defaults)
              ? (tpl.key_events_defaults as KeyEvent[])
              : []
          )
        }
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : 'Failed to load template')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => { cancelled = true }
  }, [templateId])

  /* ---- Derived: rounds count ---- */

  const maxRounds = schedule.default_rounds ?? 6

  /* ---- Derived: calculated totals (same formula as SimRunWizard) ---- */

  const totals = useMemo(() => {
    const r1 = schedule.round_1_duration_min ?? 80
    const rN = schedule.subsequent_round_duration_min ?? 60
    const breakMin = schedule.break_duration_min ?? 15
    const introMin = schedule.introduction_duration_min ?? 30
    const reflectionMin = schedule.reflection_duration_min ?? 20
    const debriefMin = schedule.debriefing_duration_min ?? 30
    const netPlay = r1 + rN * Math.max(0, maxRounds - 1)
    const totalBreaks = breakMin * Math.max(0, maxRounds - 1)
    const totalEvent = introMin + netPlay + totalBreaks + reflectionMin + debriefMin
    return { netPlay, totalBreaks, totalEvent }
  }, [schedule, maxRounds])

  /* ---- Change tracking ---- */

  const hasChanges = useMemo(() => {
    if (!template) return false
    const origSched = template.schedule_defaults ?? {}
    const origEvents = template.key_events_defaults ?? []
    return (
      JSON.stringify(schedule) !== JSON.stringify(origSched) ||
      JSON.stringify(keyEvents) !== JSON.stringify(origEvents)
    )
  }, [schedule, keyEvents, template])

  /* ---- Handlers ---- */

  const updateScheduleField = useCallback((key: string, value: number) => {
    setSchedule((prev) => ({ ...prev, [key]: value }))
  }, [])

  const updateKeyEventRound = useCallback((index: number, round: number) => {
    setKeyEvents((prev) =>
      prev.map((ev, i) => (i === index ? { ...ev, round } : ev))
    )
  }, [])

  const deleteKeyEvent = useCallback((index: number) => {
    setKeyEvents((prev) => prev.filter((_, i) => i !== index))
  }, [])

  const addKeyEvent = useCallback((event: KeyEvent) => {
    setKeyEvents((prev) => [...prev, event])
    setShowAddEvent(false)
  }, [])

  const handleSave = async () => {
    setSaving(true)
    setSaved(false)
    setError(null)
    try {
      await updateTemplate(templateId, {
        schedule_defaults: schedule,
        key_events_defaults: keyEvents as unknown[],
      })
      const refreshed = await getTemplate(templateId)
      if (refreshed) setTemplate(refreshed)
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Save failed')
    } finally {
      setSaving(false)
    }
  }

  /* ---- Render: loading / error ---- */

  if (loading) {
    return (
      <div className="py-8 text-center">
        <p className="font-body text-body-sm text-text-secondary">Loading schedule...</p>
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

  /* ---- Render ---- */

  return (
    <div className="space-y-6">
      <h3 className="font-heading text-h3 text-text-primary">Schedule Defaults</h3>

      {error && (
        <div className="bg-danger/10 border border-danger/30 rounded-lg p-3">
          <p className="font-body text-body-sm text-danger">{error}</p>
        </div>
      )}

      {/* Number of Rounds */}
      <div>
        <label className="block font-body text-body-sm text-text-primary mb-1">
          Number of Rounds
        </label>
        <input
          type="number"
          min={1}
          max={20}
          value={maxRounds}
          onChange={(e) =>
            updateScheduleField('default_rounds', Math.max(1, parseInt(e.target.value) || 1))
          }
          className="w-24 bg-base border border-border rounded px-3 py-2 font-data text-data text-text-primary focus:outline-none focus:border-action transition-colors"
        />
      </div>

      {/* Duration fields */}
      <div>
        <h4 className="font-heading text-h3 text-text-primary mb-3">Durations</h4>
        <div className="grid grid-cols-2 gap-4">
          {DURATION_FIELDS.map((key) => (
            <div key={key}>
              <label className="block font-body text-caption text-text-secondary mb-1">
                {SCHEDULE_LABELS[key] ?? key.replace(/_/g, ' ')}
              </label>
              <input
                type="number"
                min={0}
                value={schedule[key] ?? 0}
                onChange={(e) =>
                  updateScheduleField(key, Math.max(0, parseInt(e.target.value) || 0))
                }
                className="w-full bg-base border border-border rounded px-3 py-2 font-data text-data text-text-primary focus:outline-none focus:border-action transition-colors"
              />
            </div>
          ))}
        </div>
      </div>

      {/* Calculated totals */}
      <div className="bg-base border border-border rounded-lg p-4">
        <h4 className="font-heading text-h3 text-text-primary mb-2">Calculated Totals</h4>
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

      {/* Key Events */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h4 className="font-heading text-h3 text-text-primary">Key Events</h4>
          <button
            onClick={() => setShowAddEvent(true)}
            className="font-body text-body-sm text-action hover:underline"
          >
            + Add Event
          </button>
        </div>

        {showAddEvent && (
          <AddEventForm
            organizations={organizations}
            roles={roles}
            countries={countries}
            maxRounds={maxRounds}
            onAdd={addKeyEvent}
            onCancel={() => setShowAddEvent(false)}
          />
        )}

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
                  {ev.type === 'election' && ev.nominations_round != null && (
                    <span className="font-body text-caption text-text-secondary ml-2">
                      (nominations R{ev.nominations_round})
                    </span>
                  )}
                  {ev.participants && ev.participants.length > 0 && (
                    <span className="font-body text-caption text-text-secondary ml-2">
                      — {ev.participants.map((p) => cap(p.character_name)).join(', ')}
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
                  <label className="font-body text-caption text-text-secondary">R:</label>
                  <input
                    type="number"
                    min={1}
                    max={maxRounds}
                    value={ev.round}
                    onChange={(e) =>
                      updateKeyEventRound(i, Math.max(1, parseInt(e.target.value) || 1))
                    }
                    className="w-14 bg-base border border-border rounded px-2 py-1.5 font-data text-data text-text-primary focus:outline-none focus:border-action transition-colors"
                  />
                  <button
                    onClick={() => deleteKeyEvent(i)}
                    className="font-body text-caption text-danger hover:underline ml-1"
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Save button */}
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
          {saving ? 'Saving...' : 'Save Schedule'}
        </button>
        {saved && (
          <span className="font-body text-caption text-success">Saved</span>
        )}
        {hasChanges && !saving && !saved && (
          <span className="font-body text-caption text-warning">Unsaved changes</span>
        )}
      </div>
    </div>
  )
}

/* ========================================================================== */
/*  Add Event Form                                                             */
/* ========================================================================== */

const ELECTION_SUBTYPES = [
  { value: 'parliamentary_midterm', label: 'Mid-Term Parliamentary Elections' },
  { value: 'presidential', label: 'Presidential Election' },
  { value: 'wartime', label: 'Wartime Presidential Election' },
] as const

const MEETING_SUBTYPES = [
  { value: 'organization_session', label: 'Organization Session' },
  { value: 'bilateral', label: 'Bilateral Meeting' },
  { value: 'trilateral_negotiation', label: 'Trilateral / Multilateral Meeting' },
] as const

function AddEventForm({
  organizations,
  roles,
  countries,
  maxRounds,
  onAdd,
  onCancel,
}: {
  organizations: Organization[]
  roles: Role[]
  countries: Country[]
  maxRounds: number
  onAdd: (event: KeyEvent) => void
  onCancel: () => void
}) {
  const [eventType, setEventType] = useState<'election' | 'mandatory_meeting'>('election')

  // Election fields
  const [electionSubtype, setElectionSubtype] = useState('parliamentary_midterm')
  const [electionCountry, setElectionCountry] = useState('columbia')
  const [electionRound, setElectionRound] = useState(2)
  const [nominationsRound, setNominationsRound] = useState(1)

  // Meeting fields
  const [meetingSubtype, setMeetingSubtype] = useState('organization_session')
  const [selectedOrg, setSelectedOrg] = useState('')
  const [meetingName, setMeetingName] = useState('')
  const [meetingRound, setMeetingRound] = useState(1)
  const [meetingNote, setMeetingNote] = useState('')

  // Participant selection for bilateral/multilateral
  const [selectedParticipants, setSelectedParticipants] = useState<string[]>([])

  const toggleParticipant = (roleId: string) => {
    setSelectedParticipants((prev) =>
      prev.includes(roleId) ? prev.filter((id) => id !== roleId) : [...prev, roleId]
    )
  }

  const handleSubmit = () => {
    if (eventType === 'election') {
      const countryName = cap(electionCountry)
      const subtypeLabel = ELECTION_SUBTYPES.find((s) => s.value === electionSubtype)?.label ?? electionSubtype
      onAdd({
        type: 'election',
        subtype: electionSubtype,
        name: `${countryName} ${subtypeLabel}`,
        country_code: electionCountry,
        round: electionRound,
        nominations_round: nominationsRound,
      })
    } else if (meetingSubtype === 'organization_session') {
      const org = organizations.find((o) => o.id === selectedOrg)
      if (!org) return
      onAdd({
        type: 'mandatory_meeting',
        subtype: 'organization_session',
        name: meetingName || `${org.sim_name} Session`,
        organization: selectedOrg,
        round: meetingRound,
      })
    } else {
      // bilateral / trilateral
      const participants = selectedParticipants.map((roleId) => {
        const role = roles.find((r) => r.id === roleId)
        return {
          role_id: roleId,
          country_code: role?.country_id ?? '',
          character_name: role?.character_name ?? roleId,
        }
      })
      if (participants.length < 2) return
      onAdd({
        type: 'mandatory_meeting',
        subtype: meetingSubtype,
        name: meetingName || `${participants.map((p) => cap(p.character_name)).join(' — ')} Meeting`,
        participants,
        note: meetingNote || undefined,
        round: meetingRound,
      })
    }
  }

  // Group roles by country for participant picker
  const COUNTRY_ORDER = [
    'columbia', 'cathay', 'gallia', 'teutonia', 'ponte', 'freeland', 'albion',
    'sarmatia', 'ruthenia', 'persia', 'bharata', 'caribe', 'choson', 'formosa',
    'hanguk', 'levantia', 'mirage', 'phrygia', 'solaria', 'yamato',
  ]
  const sortedRoles = [...roles].sort((a, b) => {
    const ia = COUNTRY_ORDER.indexOf(a.country_id)
    const ib = COUNTRY_ORDER.indexOf(b.country_id)
    if (ia !== ib) return ia - ib
    return a.character_name.localeCompare(b.character_name)
  })

  return (
    <div className="border border-action/30 bg-action/5 rounded-lg p-4 mb-4 space-y-4">
      <h4 className="font-heading text-h3 text-text-primary">Add Key Event</h4>

      {/* Event type toggle */}
      <div className="flex gap-2">
        <button
          onClick={() => setEventType('election')}
          className={`font-body text-body-sm px-3 py-1.5 rounded transition-colors ${
            eventType === 'election'
              ? 'bg-warning/20 text-warning font-medium'
              : 'bg-base text-text-secondary hover:text-text-primary'
          }`}
        >
          Election
        </button>
        <button
          onClick={() => setEventType('mandatory_meeting')}
          className={`font-body text-body-sm px-3 py-1.5 rounded transition-colors ${
            eventType === 'mandatory_meeting'
              ? 'bg-action/20 text-action font-medium'
              : 'bg-base text-text-secondary hover:text-text-primary'
          }`}
        >
          Meeting
        </button>
      </div>

      {eventType === 'election' ? (
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block font-body text-caption text-text-secondary mb-1">Election Type</label>
              <select
                value={electionSubtype}
                onChange={(e) => setElectionSubtype(e.target.value)}
                className="w-full bg-base border border-border rounded px-3 py-2 font-body text-body-sm text-text-primary focus:outline-none focus:border-action"
              >
                {ELECTION_SUBTYPES.map((s) => (
                  <option key={s.value} value={s.value}>{s.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block font-body text-caption text-text-secondary mb-1">Country</label>
              <select
                value={electionCountry}
                onChange={(e) => setElectionCountry(e.target.value)}
                className="w-full bg-base border border-border rounded px-3 py-2 font-body text-body-sm text-text-primary focus:outline-none focus:border-action"
              >
                {countries.map((c) => (
                  <option key={c.id} value={c.id}>{cap(c.id)}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block font-body text-caption text-text-secondary mb-1">Election Round</label>
              <input
                type="number" min={1} max={maxRounds} value={electionRound}
                onChange={(e) => setElectionRound(Math.max(1, parseInt(e.target.value) || 1))}
                className="w-full bg-base border border-border rounded px-3 py-2 font-data text-data text-text-primary focus:outline-none focus:border-action"
              />
            </div>
            <div>
              <label className="block font-body text-caption text-text-secondary mb-1">Nominations Round</label>
              <input
                type="number" min={1} max={maxRounds} value={nominationsRound}
                onChange={(e) => setNominationsRound(Math.max(1, parseInt(e.target.value) || 1))}
                className="w-full bg-base border border-border rounded px-3 py-2 font-data text-data text-text-primary focus:outline-none focus:border-action"
              />
            </div>
          </div>
        </div>
      ) : (
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block font-body text-caption text-text-secondary mb-1">Meeting Type</label>
              <select
                value={meetingSubtype}
                onChange={(e) => setMeetingSubtype(e.target.value)}
                className="w-full bg-base border border-border rounded px-3 py-2 font-body text-body-sm text-text-primary focus:outline-none focus:border-action"
              >
                {MEETING_SUBTYPES.map((s) => (
                  <option key={s.value} value={s.value}>{s.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block font-body text-caption text-text-secondary mb-1">Round</label>
              <input
                type="number" min={1} max={maxRounds} value={meetingRound}
                onChange={(e) => setMeetingRound(Math.max(1, parseInt(e.target.value) || 1))}
                className="w-full bg-base border border-border rounded px-3 py-2 font-data text-data text-text-primary focus:outline-none focus:border-action"
              />
            </div>
          </div>

          {meetingSubtype === 'organization_session' ? (
            <div>
              <label className="block font-body text-caption text-text-secondary mb-1">Organization</label>
              <select
                value={selectedOrg}
                onChange={(e) => setSelectedOrg(e.target.value)}
                className="w-full bg-base border border-border rounded px-3 py-2 font-body text-body-sm text-text-primary focus:outline-none focus:border-action"
              >
                <option value="">Select organization...</option>
                {organizations.map((o) => (
                  <option key={o.id} value={o.id}>{o.sim_name} ({o.parallel})</option>
                ))}
              </select>
            </div>
          ) : (
            <div>
              <label className="block font-body text-caption text-text-secondary mb-2">
                Select Participants ({selectedParticipants.length} selected)
              </label>
              <div className="max-h-48 overflow-y-auto border border-border rounded p-2 space-y-0.5">
                {sortedRoles.map((role) => (
                  <label
                    key={role.id}
                    className={`flex items-center gap-2 px-2 py-1 rounded cursor-pointer hover:bg-base transition-colors ${
                      selectedParticipants.includes(role.id) ? 'bg-action/10' : ''
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={selectedParticipants.includes(role.id)}
                      onChange={() => toggleParticipant(role.id)}
                      className="accent-action"
                    />
                    <span className="font-body text-body-sm text-text-primary">
                      {role.character_name}
                    </span>
                    <span className="font-body text-caption text-text-secondary">
                      — {cap(role.country_id)}, {role.title}
                    </span>
                  </label>
                ))}
              </div>
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block font-body text-caption text-text-secondary mb-1">Meeting Name (optional)</label>
              <input
                type="text" value={meetingName}
                onChange={(e) => setMeetingName(e.target.value)}
                placeholder="Auto-generated if empty"
                className="w-full bg-base border border-border rounded px-3 py-2 font-body text-body-sm text-text-primary placeholder:text-text-secondary/50 focus:outline-none focus:border-action"
              />
            </div>
            <div>
              <label className="block font-body text-caption text-text-secondary mb-1">Note (optional)</label>
              <input
                type="text" value={meetingNote}
                onChange={(e) => setMeetingNote(e.target.value)}
                placeholder="e.g. Representatives, not HoS"
                className="w-full bg-base border border-border rounded px-3 py-2 font-body text-body-sm text-text-primary placeholder:text-text-secondary/50 focus:outline-none focus:border-action"
              />
            </div>
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-2">
        <button
          onClick={handleSubmit}
          className="bg-action text-white font-body text-body-sm font-medium py-2 px-4 rounded hover:opacity-90 transition-opacity"
        >
          Add Event
        </button>
        <button
          onClick={onCancel}
          className="bg-base border border-border text-text-secondary font-body text-body-sm font-medium py-2 px-4 rounded hover:bg-border/30 transition-colors"
        >
          Cancel
        </button>
      </div>
    </div>
  )
}
