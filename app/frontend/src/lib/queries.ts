/**
 * Supabase query functions — centralized data access layer.
 * All DB reads/writes go through here.
 */

import { supabase } from '@/lib/supabase'

/** Engine API base URL. Empty in dev (Vite proxy), set via VITE_API_URL in production. */
const API_BASE = import.meta.env.VITE_API_URL ?? ''

/* -------------------------------------------------------------------------- */
/*  Types                                                                     */
/* -------------------------------------------------------------------------- */

export interface SimTemplate {
  id: string
  code: string
  name: string
  version: string
  description: string | null
  status: string
  schedule_defaults: Record<string, number>
  key_events_defaults: unknown[]
  formula_coefficients: Record<string, unknown> | null
  created_at: string
}

export interface SimRun {
  id: string
  name: string
  status: string
  current_round: number
  current_phase: string
  template_id: string | null
  facilitator_id: string | null
  logo_url: string | null
  schedule: Record<string, number>
  key_events: unknown[]
  max_rounds: number
  human_participants: number
  ai_participants: number
  description: string | null
  created_at: string
  started_at: string | null
  completed_at: string | null
  auto_approve?: boolean
  auto_attack?: boolean
  dice_mode?: boolean
  nominations_open?: boolean
  nominations_closed?: boolean
  election_open?: boolean
  election_stopped?: boolean
  election_started_at?: string | null
  election_duration_min?: number
  election_econ_score?: number | null
  election_stability?: number | null
  election_inflation?: number | null
}

export interface SimRunRole {
  id: string
  sim_run_id: string
  character_name: string
  country_code: string
  title: string
  positions: string[]
  position_type: string
  is_ai_operated: boolean
  expansion_role: boolean
  public_bio: string
  status: string
  user_id: string | null
}

export interface UserRecord {
  id: string
  email: string
  display_name: string
  system_role: string
  status: string
  data_consent: boolean
  created_at: string
  last_login_at: string | null
}

/* -------------------------------------------------------------------------- */
/*  Templates                                                                 */
/* -------------------------------------------------------------------------- */

export async function getTemplates(): Promise<SimTemplate[]> {
  const { data, error } = await supabase
    .from('sim_templates')
    .select('id, code, name, version, description, status, schedule_defaults, key_events_defaults, created_at')
    .order('created_at', { ascending: false })

  if (error) throw error
  return (data ?? []) as SimTemplate[]
}

export async function getTemplate(id: string): Promise<SimTemplate | null> {
  const { data, error } = await supabase
    .from('sim_templates')
    .select('*')
    .eq('id', id)
    .single()

  if (error) return null
  return data as SimTemplate
}

/* -------------------------------------------------------------------------- */
/*  SimRuns                                                                   */
/* -------------------------------------------------------------------------- */

export async function getSimRuns(): Promise<SimRun[]> {
  const { data, error } = await supabase
    .from('sim_runs')
    .select('*')
    .order('created_at', { ascending: false })
    .limit(20)

  if (error) throw error
  return (data ?? []) as SimRun[]
}

export async function getSimRun(id: string): Promise<SimRun | null> {
  const { data, error } = await supabase
    .from('sim_runs')
    .select('*')
    .eq('id', id)
    .single()

  if (error) return null
  return data as SimRun
}

export interface RoleCustomization {
  role_id: string
  active: boolean
  is_ai_operated: boolean
}

export async function createSimRun(params: {
  name: string
  template_id: string
  schedule: Record<string, number>
  key_events: unknown[]
  max_rounds: number
  logo_url?: string
  description?: string
  role_customizations?: RoleCustomization[]
}): Promise<SimRun> {
  const token = await getToken()
  const resp = await fetch('/api/sim/create', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({
      name: params.name,
      template_id: params.template_id,
      schedule: params.schedule,
      key_events: params.key_events,
      max_rounds: params.max_rounds,
      logo_url: params.logo_url ?? null,
      description: params.description ?? null,
      role_customizations: params.role_customizations ?? [],
    }),
  })
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ error: 'Creation failed' }))
    throw new Error(err.detail || err.error || 'SimRun creation failed')
  }
  const result = await resp.json()
  return result.data as SimRun
}

export async function updateSimRun(
  id: string,
  updates: Partial<SimRun>
): Promise<void> {
  const { error } = await supabase
    .from('sim_runs')
    .update(updates)
    .eq('id', id)

  if (error) throw error
}

export async function deleteSimRun(id: string): Promise<void> {
  const { error } = await supabase
    .from('sim_runs')
    .delete()
    .eq('id', id)

  if (error) throw error
}

export async function duplicateSimRun(sourceId: string, newName: string): Promise<SimRun> {
  const source = await getSimRun(sourceId)
  if (!source) throw new Error('SimRun not found')

  // Use server-side creation to copy all game data
  return createSimRun({
    name: newName,
    template_id: source.template_id ?? '',
    schedule: source.schedule,
    key_events: source.key_events as unknown[],
    max_rounds: source.max_rounds,
    logo_url: source.logo_url ?? undefined,
    description: source.description ?? undefined,
    // No role_customizations → copies all roles as-is
  })
}

/* -------------------------------------------------------------------------- */
/*  Roles (per SimRun)                                                        */
/* -------------------------------------------------------------------------- */

export async function getSimRunRoles(simRunId: string): Promise<SimRunRole[]> {
  const { data, error } = await supabase
    .from('roles')
    .select('id, sim_run_id, character_name, country_code, title, position_type, positions, is_ai_operated, expansion_role, public_bio, status, user_id')
    .eq('sim_run_id', simRunId)
    .order('country_code')

  if (error) throw error
  return (data ?? []) as SimRunRole[]
}

/* -------------------------------------------------------------------------- */
/*  Users (admin)                                                             */
/* -------------------------------------------------------------------------- */

export async function getAllUsers(): Promise<UserRecord[]> {
  const { data, error } = await supabase
    .from('users')
    .select('id, email, display_name, system_role, status, data_consent, created_at, last_login_at')
    .order('created_at', { ascending: false })

  if (error) throw error
  return (data ?? []) as UserRecord[]
}

export async function updateUserStatus(
  userId: string,
  status: string
): Promise<void> {
  const { error } = await supabase
    .from('users')
    .update({ status })
    .eq('id', userId)

  if (error) throw error
}

export async function assignUserToRole(
  simRunId: string,
  roleId: string,
  userId: string | null,
): Promise<void> {
  const { error } = await supabase
    .from('roles')
    .update({ user_id: userId })
    .eq('sim_run_id', simRunId)
    .eq('id', roleId)

  if (error) throw error
}

export async function toggleRoleAI(
  simRunId: string,
  roleId: string,
  isAI: boolean,
): Promise<void> {
  const { error } = await supabase
    .from('roles')
    .update({ is_ai_operated: isAI, user_id: null })
    .eq('sim_run_id', simRunId)
    .eq('id', roleId)

  if (error) throw error
}

export async function randomAssignRoles(
  simRunId: string,
  userIds: string[],
): Promise<number> {
  // Get unassigned human roles
  const { data: roles } = await supabase
    .from('roles')
    .select('id')
    .eq('sim_run_id', simRunId)
    .eq('is_ai_operated', false)
    .is('user_id', null)
    .eq('status', 'active')

  if (!roles || roles.length === 0) return 0

  // Shuffle users (Fisher-Yates)
  const shuffled = [...userIds]
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]]
  }

  // Assign up to min(users, roles)
  const count = Math.min(shuffled.length, roles.length)
  for (let i = 0; i < count; i++) {
    await supabase
      .from('roles')
      .update({ user_id: shuffled[i] })
      .eq('sim_run_id', simRunId)
      .eq('id', roles[i].id)
  }
  return count
}

export async function deleteUser(userId: string): Promise<void> {
  const { error } = await supabase
    .from('users')
    .delete()
    .eq('id', userId)

  if (error) throw error
}

/* -------------------------------------------------------------------------- */
/*  Global Config (LLM models)                                                */
/* -------------------------------------------------------------------------- */

export async function getGlobalConfig(
  category: string
): Promise<Record<string, string>> {
  const { data, error } = await supabase
    .from('sim_config')
    .select('key, content')
    .eq('category', category)
    .eq('is_active', true)

  if (error) throw error
  const result: Record<string, string> = {}
  for (const row of data ?? []) {
    result[row.key] = row.content
  }
  return result
}

export async function setGlobalConfig(
  category: string,
  key: string,
  content: string,
  templateId: string
): Promise<void> {
  // Upsert: try update first, then insert if not found
  const { data: existing } = await supabase
    .from('sim_config')
    .select('id')
    .eq('category', category)
    .eq('key', key)
    .single()

  if (existing) {
    const { error } = await supabase
      .from('sim_config')
      .update({ content, updated_at: new Date().toISOString() })
      .eq('category', category)
      .eq('key', key)

    if (error) throw error
  } else {
    const { error } = await supabase
      .from('sim_config')
      .insert({
        template_id: templateId,
        category,
        key,
        content,
        version: 1,
        is_active: true,
      })

    if (error) throw error
  }
}

/* -------------------------------------------------------------------------- */
/*  Template CRUD                                                             */
/* -------------------------------------------------------------------------- */

export async function createTemplate(params: {
  code: string
  name: string
  version: string
  description?: string
}): Promise<SimTemplate> {
  const { data, error } = await supabase
    .from('sim_templates')
    .insert({
      code: params.code,
      name: params.name,
      version: params.version,
      description: params.description ?? null,
      status: 'draft',
      schedule_defaults: {},
      key_events_defaults: [],
    })
    .select()
    .single()

  if (error) throw error
  return data as SimTemplate
}

export async function updateTemplate(
  id: string,
  updates: Partial<SimTemplate>
): Promise<void> {
  const { error } = await supabase
    .from('sim_templates')
    .update(updates)
    .eq('id', id)

  if (error) throw error
}

export async function deleteTemplate(id: string): Promise<void> {
  const { error } = await supabase
    .from('sim_templates')
    .delete()
    .eq('id', id)

  if (error) throw error
}

export async function duplicateTemplate(
  sourceId: string,
  newName: string
): Promise<SimTemplate> {
  const source = await getTemplate(sourceId)
  if (!source) throw new Error('Template not found')

  const { data, error } = await supabase
    .from('sim_templates')
    .insert({
      code: `${source.code}_copy`,
      name: newName,
      version: source.version,
      description: source.description,
      status: 'draft',
      schedule_defaults: source.schedule_defaults,
      key_events_defaults: source.key_events_defaults,
    })
    .select()
    .single()

  if (error) throw error
  return data as SimTemplate
}

/* -------------------------------------------------------------------------- */
/*  Template Data (reads from reference sim_run)                              */
/* -------------------------------------------------------------------------- */

const DEFAULT_SIM_RUN_ID = '00000000-0000-0000-0000-000000000001'

export interface Country {
  id: string
  sim_run_id: string
  sim_name: string
  parallel: string
  regime_type: string
  team_type: string
  team_size_min: number
  team_size_max: number
  ai_default: boolean
  gdp: number
  gdp_growth_base: number
  sector_resources: number
  sector_industry: number
  sector_services: number
  sector_technology: number
  tax_rate: number
  treasury: number
  inflation: number
  trade_balance: number
  oil_producer: boolean
  opec_member: boolean
  opec_production: string
  oil_production_mbpd: number
  formosa_dependency: number
  debt_burden: number
  debt_ratio: number
  social_baseline: number
  sanctions_coefficient: number
  tariff_coefficient: number
  mil_ground: number
  mil_naval: number
  mil_tactical_air: number
  mil_strategic_missiles: number
  mil_air_defense: number
  prod_cost_ground: number
  prod_cost_naval: number
  prod_cost_tactical: number
  prod_cap_ground: number
  prod_cap_naval: number
  prod_cap_tactical: number
  maintenance_per_unit: number
  strategic_missile_growth: number
  mobilization_pool: number
  stability: number
  war_tiredness: number
  nuclear_level: number
  nuclear_rd_progress: number
  ai_level: number
  ai_rd_progress: number
  home_zones: string
  color_ui: string
  color_map: string
  color_light: string
  country_brief: string | null
}

export interface Role {
  id: string
  sim_run_id: string
  character_name: string
  parallel: string
  country_code: string
  team: string
  faction: string
  title: string
  age: number
  gender: string
  is_head_of_state: boolean
  is_military_chief: boolean
  is_economy_officer: boolean
  is_diplomat: boolean
  parliament_seat: number
  personal_coins: number
  expansion_role: boolean
  ai_candidate: boolean
  is_ai_operated: boolean
  brief_file: string
  public_bio: string
  confidential_brief: string
  positions: string[]
  position_type: string
  party: string
  intelligence_pool: number
  sabotage_cards: number
  cyber_cards: number
  disinfo_cards: number
  election_meddling_cards: number
  assassination_cards: number
  protest_stim_cards: number
  powers: string[]
  objectives: string[]
  status: string
}

export interface Organization {
  id: string
  sim_run_id: string
  sim_name: string
  parallel: string
  decision_rule: string
  chair_role_id: string
  voting_threshold: string
  meeting_frequency: string
  can_be_created: boolean
  description: string
}

export interface OrgMembership {
  id: string
  sim_run_id: string
  country_code: string
  org_id: string
  role_id: string | null
  role_in_org: string
  has_veto: boolean
  seat_type: string
}

export interface Relationship {
  id: string
  sim_run_id: string
  from_country_code: string
  to_country_code: string
  relationship: string
  status: string
  dynamic: string
  basing_rights_a_to_b: boolean
  basing_rights_b_to_a: boolean
}

export interface Sanction {
  id: string
  sim_run_id: string
  imposer_country_code: string
  target_country_code: string
  level: number
  notes: string
}

export interface Tariff {
  id: string
  sim_run_id: string
  imposer_country_code: string
  target_country_code: string
  level: number
  notes: string
}

export interface Zone {
  id: string
  sim_run_id: string
  display_name: string
  type: string
  owner: string
  controlled_by: string | null
  theater: string
  is_chokepoint: boolean
  die_hard: boolean
}

export interface Deployment {
  id: string
  sim_run_id: string
  unit_id: string | null
  country_code: string
  unit_type: string
  global_row: number | null
  global_col: number | null
  theater: string | null
  theater_row: number | null
  theater_col: number | null
  embarked_on: string | null
  unit_status: string
  count: number
  notes: string
}

export async function getTemplateCountries(): Promise<Country[]> {
  const { data, error } = await supabase
    .from('countries')
    .select('*')
    .eq('sim_run_id', DEFAULT_SIM_RUN_ID)
    .order('id')
  if (error) throw error
  return (data ?? []) as Country[]
}

export async function updateCountry(id: string, updates: Partial<Country>): Promise<void> {
  const { sim_run_id, ...rest } = updates as Record<string, unknown>
  const { error } = await supabase
    .from('countries')
    .update(rest)
    .eq('id', id)
    .eq('sim_run_id', DEFAULT_SIM_RUN_ID)
  if (error) throw error
}

export async function createCountry(country: Partial<Country> & { id: string; sim_name: string }): Promise<void> {
  const { error } = await supabase
    .from('countries')
    .insert({ sim_run_id: DEFAULT_SIM_RUN_ID, ...country })
  if (error) throw error
}

export async function deleteCountry(id: string): Promise<void> {
  const { error } = await supabase
    .from('countries')
    .delete()
    .eq('id', id)
    .eq('sim_run_id', DEFAULT_SIM_RUN_ID)
  if (error) throw error
}

export async function getTemplateRoles(): Promise<Role[]> {
  const { data, error } = await supabase
    .from('roles')
    .select('*')
    .eq('sim_run_id', DEFAULT_SIM_RUN_ID)
    .order('country_code, character_name')
  if (error) throw error
  return (data ?? []) as Role[]
}

export async function updateRole(id: string, updates: Partial<Role>): Promise<void> {
  const { sim_run_id, ...rest } = updates as Record<string, unknown>
  const { error } = await supabase
    .from('roles')
    .update(rest)
    .eq('id', id)
    .eq('sim_run_id', DEFAULT_SIM_RUN_ID)
  if (error) throw error
}

export async function createRole(role: Partial<Role> & { id: string; character_name: string; country_code: string }): Promise<void> {
  const { error } = await supabase
    .from('roles')
    .insert({ sim_run_id: DEFAULT_SIM_RUN_ID, ...role })
  if (error) throw error
}

export async function deleteRole(id: string): Promise<void> {
  const { error } = await supabase
    .from('roles')
    .delete()
    .eq('id', id)
    .eq('sim_run_id', DEFAULT_SIM_RUN_ID)
  if (error) throw error
}

export async function getTemplateOrganizations(): Promise<Organization[]> {
  const { data, error } = await supabase
    .from('organizations')
    .select('*')
    .eq('sim_run_id', DEFAULT_SIM_RUN_ID)
    .order('sim_name')
  if (error) throw error
  return (data ?? []) as Organization[]
}

export async function updateOrganization(id: string, updates: Partial<Organization>): Promise<void> {
  const { sim_run_id, ...rest } = updates as Record<string, unknown>
  const { error } = await supabase
    .from('organizations')
    .update(rest)
    .eq('id', id)
    .eq('sim_run_id', DEFAULT_SIM_RUN_ID)
  if (error) throw error
}

export async function getTemplateOrgMemberships(): Promise<OrgMembership[]> {
  const { data, error } = await supabase
    .from('org_memberships')
    .select('*')
    .eq('sim_run_id', DEFAULT_SIM_RUN_ID)
  if (error) throw error
  return (data ?? []) as OrgMembership[]
}

export async function getTemplateRelationships(): Promise<Relationship[]> {
  const { data, error } = await supabase
    .from('relationships')
    .select('*')
    .eq('sim_run_id', DEFAULT_SIM_RUN_ID)
    .order('from_country_code, to_country_code')
  if (error) throw error
  return (data ?? []) as Relationship[]
}

export async function updateRelationship(id: string, updates: Partial<Relationship>): Promise<void> {
  const { sim_run_id, ...rest } = updates as Record<string, unknown>
  const { error } = await supabase
    .from('relationships')
    .update(rest)
    .eq('id', id)
    .eq('sim_run_id', DEFAULT_SIM_RUN_ID)
  if (error) throw error
}

export async function getTemplateSanctions(): Promise<Sanction[]> {
  const { data, error } = await supabase
    .from('sanctions')
    .select('*')
    .eq('sim_run_id', DEFAULT_SIM_RUN_ID)
    .order('imposer_country_code, target_country_code')
  if (error) throw error
  return (data ?? []) as Sanction[]
}

export async function getTemplateTariffs(): Promise<Tariff[]> {
  const { data, error } = await supabase
    .from('tariffs')
    .select('*')
    .eq('sim_run_id', DEFAULT_SIM_RUN_ID)
    .order('imposer_country_code, target_country_code')
  if (error) throw error
  return (data ?? []) as Tariff[]
}

export async function getTemplateZones(): Promise<Zone[]> {
  const { data, error } = await supabase
    .from('zones')
    .select('*')
    .eq('sim_run_id', DEFAULT_SIM_RUN_ID)
    .order('theater, id')
  if (error) throw error
  return (data ?? []) as Zone[]
}

export interface RoleAction {
  id: string
  sim_run_id: string
  role_id: string
  action_id: string
  uses_per_round: number | null
  uses_total: number | null
  notes: string
}

export interface RoleRelationship {
  id: string
  sim_run_id: string
  role_a_id: string
  role_b_id: string
  relationship_type: string
  notes: string
}

export async function getTemplateRoleActions(): Promise<RoleAction[]> {
  const { data, error } = await supabase
    .from('role_actions')
    .select('*')
    .eq('sim_run_id', DEFAULT_SIM_RUN_ID)
    .order('role_id, action_id')
  if (error) throw error
  return (data ?? []) as RoleAction[]
}

export async function getTemplateRoleRelationships(): Promise<RoleRelationship[]> {
  const { data, error } = await supabase
    .from('role_relationships')
    .select('*')
    .eq('sim_run_id', DEFAULT_SIM_RUN_ID)
    .order('role_a_id, role_b_id')
  if (error) throw error
  return (data ?? []) as RoleRelationship[]
}

export async function getTemplateDeployments(): Promise<Deployment[]> {
  const { data, error } = await supabase
    .from('deployments')
    .select('*')
    .eq('sim_run_id', DEFAULT_SIM_RUN_ID)
    .order('country_code, unit_type, global_row, global_col')
  if (error) throw error
  return (data ?? []) as Deployment[]
}

/* -------------------------------------------------------------------------- */
/*  Sim Runner API helpers                                                    */
/* -------------------------------------------------------------------------- */

/** Fetch live sim state from the Sim Runner API. */
export async function getSimState(simId: string): Promise<Record<string, unknown>> {
  const token = await getToken()
  const resp = await fetch(`${API_BASE}/api/sim/${simId}/state`, {
    headers: token ? { 'Authorization': `Bearer ${token}` } : {},
  })
  if (!resp.ok) throw new Error('Failed to get sim state')
  const data = await resp.json()
  return data.data
}

/** Submit a game action (public_statement, set_budget, etc.). */
export async function submitAction(
  simId: string,
  actionType: string,
  roleId: string,
  countryCode: string,
  params?: Record<string, unknown>
): Promise<Record<string, unknown>> {
  const token = await getToken()
  const resp = await fetch(`${API_BASE}/api/sim/${simId}/action`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({
      action_type: actionType,
      role_id: roleId,
      country_code: countryCode,
      params: params ?? {},
    }),
  })
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ error: 'Action failed' }))
    throw new Error(err.detail || err.error || 'Action submission failed')
  }
  const data = await resp.json()
  return data.data
}

/** Execute a sim control action (start, pause, resume, phase/end, etc.). */
// Cache auth token to avoid getSession() blocking during heavy realtime traffic
let _cachedToken: string | null = null
let _tokenExpiry = 0
export async function getToken(): Promise<string> {
  if (_cachedToken && Date.now() < _tokenExpiry) return _cachedToken
  const { data } = await supabase.auth.getSession()
  _cachedToken = data.session?.access_token ?? ''
  _tokenExpiry = Date.now() + 300000 // 5 min cache
  return _cachedToken
}
/** Invalidate cached token — call on 401 to force refresh on next request. */
export function invalidateToken(): void {
  _cachedToken = null
  _tokenExpiry = 0
}
// Refresh token on auth state change
supabase.auth.onAuthStateChange((_event, session) => {
  _cachedToken = session?.access_token ?? null
  _tokenExpiry = session ? Date.now() + 300000 : 0
})

export async function simAction(
  simId: string,
  action: string,
  params?: Record<string, unknown>
): Promise<Record<string, unknown>> {
  const token = await getToken()
  let resp = await fetch(`${API_BASE}/api/sim/${simId}/${action}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: params ? JSON.stringify(params) : undefined,
  })
  // On 401, invalidate token and retry once
  if (resp.status === 401) {
    invalidateToken()
    const freshToken = await getToken()
    resp = await fetch(`${API_BASE}/api/sim/${simId}/${action}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${freshToken}`,
      },
      body: params ? JSON.stringify(params) : undefined,
    })
  }
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ error: 'Unknown error' }))
    throw new Error(err.detail || err.error || 'Action failed')
  }
  const data = await resp.json()
  return data.data
}

/* -------------------------------------------------------------------------- */
/*  Meeting Chat API                                                          */
/* -------------------------------------------------------------------------- */

export interface MeetingMessage {
  id: string
  meeting_id: string
  role_id: string
  country_code: string
  content: string
  channel: 'text' | 'system'
  turn_number: number
  created_at: string
}

export interface MeetingData {
  id: string
  sim_run_id: string
  invitation_id: string
  round_num: number | null
  participant_a_role_id: string
  participant_a_country: string
  participant_b_role_id: string
  participant_b_country: string
  agenda: string | null
  status: 'active' | 'completed'
  turn_count: number
  max_turns: number
  modality: string
  ended_at: string | null
  created_at: string
}

/** Fetch meeting details + all messages. */
export async function getMeetingDetail(
  simId: string,
  meetingId: string,
): Promise<{ meeting: MeetingData; messages: MeetingMessage[] }> {
  const token = await getToken()
  let resp = await fetch(`${API_BASE}/api/sim/${simId}/meetings/${meetingId}`, {
    headers: {
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    },
  })
  // On 401, invalidate token and retry once with a fresh token
  if (resp.status === 401) {
    invalidateToken()
    const freshToken = await getToken()
    resp = await fetch(`${API_BASE}/api/sim/${simId}/meetings/${meetingId}`, {
      headers: {
        ...(freshToken ? { 'Authorization': `Bearer ${freshToken}` } : {}),
      },
    })
  }
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ error: 'Failed to load meeting' }))
    throw new Error(err.detail || err.error || 'Failed to load meeting')
  }
  const json = await resp.json()
  return json.data as { meeting: MeetingData; messages: MeetingMessage[] }
}

/** Send a message in a meeting. */
export async function sendMeetingMessage(
  simId: string,
  meetingId: string,
  roleId: string,
  countryCode: string,
  content: string,
): Promise<Record<string, unknown>> {
  const token = await getToken()
  let resp = await fetch(`${API_BASE}/api/sim/${simId}/meetings/${meetingId}/message`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ role_id: roleId, country_code: countryCode, content }),
  })
  // On 401, invalidate token and retry once with a fresh token
  if (resp.status === 401) {
    invalidateToken()
    const freshToken = await getToken()
    resp = await fetch(`${API_BASE}/api/sim/${simId}/meetings/${meetingId}/message`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(freshToken ? { 'Authorization': `Bearer ${freshToken}` } : {}),
      },
      body: JSON.stringify({ role_id: roleId, country_code: countryCode, content }),
    })
  }
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ error: 'Failed to send message' }))
    throw new Error(err.detail || err.error || 'Failed to send message')
  }
  const json = await resp.json()
  return json.data
}

/** End a meeting. */
export async function endMeeting(
  simId: string,
  meetingId: string,
  roleId: string,
): Promise<Record<string, unknown>> {
  const token = await getToken()
  let resp = await fetch(`${API_BASE}/api/sim/${simId}/meetings/${meetingId}/end`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ role_id: roleId }),
  })
  // On 401, invalidate token and retry once with a fresh token
  if (resp.status === 401) {
    invalidateToken()
    const freshToken = await getToken()
    resp = await fetch(`${API_BASE}/api/sim/${simId}/meetings/${meetingId}/end`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(freshToken ? { 'Authorization': `Bearer ${freshToken}` } : {}),
      },
      body: JSON.stringify({ role_id: roleId }),
    })
  }
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ error: 'Failed to end meeting' }))
    throw new Error(err.detail || err.error || 'Failed to end meeting')
  }
  const json = await resp.json()
  return json.data
}

/** Fetch active meetings for a role. */
export async function getActiveMeetings(
  simId: string,
  roleId: string,
): Promise<MeetingData[]> {
  const token = await getToken()
  const resp = await fetch(`${API_BASE}/api/sim/${simId}/meetings/active/${roleId}`, {
    headers: {
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    },
  })
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ error: 'Failed to load meetings' }))
    throw new Error(err.detail || err.error || 'Failed to load meetings')
  }
  const json = await resp.json()
  return (json.data ?? []) as MeetingData[]
}

/* -------------------------------------------------------------------------- */
/*  AI Participant Observability (M5.6)                                       */
/* -------------------------------------------------------------------------- */

/** Per-agent cost breakdown from the orchestrator. */
export interface AIAgentCost {
  model: string
  input_tokens: number
  output_tokens: number
  input_cost_usd: number
  output_cost_usd: number
  total_cost_usd: number
  events_sent: number
  actions_submitted: number
  tool_calls: number
}

/** Per-agent round stats. */
export interface AIAgentRoundStats {
  actions: number
  tool_calls: number
  meetings_used: number
  pulses_received: number
  errors: number
}

/** Single agent status entry from /ai/status. */
export interface AIAgentStatus {
  role_id: string
  country_code: string
  state: 'IDLE' | 'ACTING' | 'IN_MEETING' | 'FROZEN' | 'TERMINATED' | string
  session_id: string
  round_num: number
  cost: AIAgentCost
  round_stats: AIAgentRoundStats
}

/** Full response from GET /api/sim/{sim_id}/ai/status. */
export interface AIStatusResponse {
  sim_run_id: string
  round_num: number
  pulse_num: number
  total_agents: number
  agents_idle: number
  agents_frozen: number
  agents_in_meeting: number
  agents_acting: number
  total_input_tokens: number
  total_output_tokens: number
  total_cost_usd: number
  agents: AIAgentStatus[]
}

/** Agent log entry from observatory_events. */
export interface AgentLogEntry {
  id: string
  sim_run_id: string
  round_num: number
  event_type: string
  country_code: string | null
  summary: string
  payload: Record<string, unknown> | null
  phase: string | null
  category: string | null
  role_name: string | null
  created_at: string
}

/** Agent memory note from agent_memories. */
export interface AgentMemory {
  id: string
  sim_run_id: string
  country_code: string
  role_id: string
  round_num: number
  memory_type: string
  content: string
  created_at: string
}

/** Fetch AI status from the orchestrator. Returns null if no orchestrator active. */
export async function getAIStatus(simId: string): Promise<AIStatusResponse | null> {
  const token = await getToken()
  const resp = await fetch(`${API_BASE}/api/sim/${simId}/ai/status`, {
    headers: token ? { 'Authorization': `Bearer ${token}` } : {},
  })
  if (resp.status === 404) return null
  if (!resp.ok) throw new Error('Failed to get AI status')
  const json = await resp.json()
  return json.data as AIStatusResponse
}

/** Initialize AI agents for a sim run. */
export async function initializeAIAgents(simId: string): Promise<Record<string, unknown>> {
  const token = await getToken()
  const resp = await fetch(`${API_BASE}/api/sim/${simId}/ai/initialize`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({}),
  })
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: 'Initialize failed' }))
    throw new Error(err.detail || 'Failed to initialize AI agents')
  }
  const json = await resp.json()
  return json.data
}

/** Freeze one AI agent. */
export async function freezeAgent(simId: string, roleId: string): Promise<void> {
  const token = await getToken()
  const resp = await fetch(`${API_BASE}/api/sim/${simId}/ai/freeze/${roleId}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    },
  })
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ error: 'Freeze failed' }))
    throw new Error(err.detail || err.error || 'Freeze failed')
  }
}

/** Resume one frozen AI agent. */
export async function resumeAgent(simId: string, roleId: string): Promise<void> {
  const token = await getToken()
  const resp = await fetch(`${API_BASE}/api/sim/${simId}/ai/resume/${roleId}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    },
  })
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ error: 'Resume failed' }))
    throw new Error(err.detail || err.error || 'Resume failed')
  }
}

/** Freeze all AI agents — global pause. */
export async function freezeAllAgents(simId: string): Promise<void> {
  const token = await getToken()
  const resp = await fetch(`${API_BASE}/api/sim/${simId}/ai/freeze-all`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    },
  })
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ error: 'Freeze all failed' }))
    throw new Error(err.detail || err.error || 'Freeze all failed')
  }
}

/** Resume all frozen AI agents. */
export async function resumeAllAgents(simId: string): Promise<void> {
  const token = await getToken()
  const resp = await fetch(`${API_BASE}/api/sim/${simId}/ai/resume-all`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    },
  })
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ error: 'Resume all failed' }))
    throw new Error(err.detail || err.error || 'Resume all failed')
  }
}

/** Shutdown all AI agents — archive sessions, clean up. */
export async function shutdownAIAgents(simId: string): Promise<void> {
  const token = await getToken()
  const resp = await fetch(`${API_BASE}/api/sim/${simId}/ai/shutdown`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    },
  })
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ error: 'Shutdown failed' }))
    throw new Error(err.detail || err.error || 'Shutdown failed')
  }
}

/** STOP ALL AI — freeze all agents + clear pending event queues. Emergency brake. */
export async function stopAllAgents(simId: string): Promise<{ frozen_count: number; events_cleared: number }> {
  const token = await getToken()
  const resp = await fetch(`${API_BASE}/api/sim/${simId}/ai/stop-all`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    },
  })
  const json = await resp.json()
  if (!resp.ok) throw new Error(json.detail || json.error || 'Stop all failed')
  return json.data
}

/** Get all global AI settings. */
export async function getAISettings(): Promise<Record<string, string>> {
  const token = await getToken()
  const resp = await fetch(`${API_BASE}/api/ai-settings`, {
    headers: { ...(token ? { 'Authorization': `Bearer ${token}` } : {}) },
  })
  const json = await resp.json()
  if (!resp.ok) throw new Error(json.detail || json.error || 'Failed to load AI settings')
  return json.data?.settings || {}
}

/** Update a single global AI setting. */
export async function updateAISetting(key: string, value: string): Promise<{ needs_reinit: boolean; message: string }> {
  const token = await getToken()
  const resp = await fetch(`${API_BASE}/api/ai-settings/${key}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ value }),
  })
  const json = await resp.json()
  if (!resp.ok) throw new Error(json.detail || json.error || 'Failed to update setting')
  return json.data
}

/** Fetch AI agent log entries from observatory_events. */
export async function getAgentLog(
  simId: string,
  countryCode?: string,
  limit: number = 50,
): Promise<AgentLogEntry[]> {
  const token = await getToken()
  const params = new URLSearchParams({ limit: String(limit) })
  if (countryCode) params.set('country_code', countryCode)
  const resp = await fetch(`${API_BASE}/api/sim/${simId}/agent-log?${params}`, {
    headers: token ? { 'Authorization': `Bearer ${token}` } : {},
  })
  if (!resp.ok) throw new Error('Failed to get agent log')
  const json = await resp.json()
  return (json.data ?? []) as AgentLogEntry[]
}

/** Fetch agent memory notes from agent_memories table. */
export async function getAgentMemories(
  simId: string,
  countryCode: string,
): Promise<AgentMemory[]> {
  const { data, error } = await supabase
    .from('agent_memories')
    .select('*')
    .eq('sim_run_id', simId)
    .eq('country_code', countryCode)
    .order('round_num', { ascending: false })

  if (error) throw error
  return (data ?? []) as AgentMemory[]
}
