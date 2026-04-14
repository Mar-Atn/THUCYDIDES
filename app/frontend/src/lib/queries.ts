/**
 * Supabase query functions — centralized data access layer.
 * All DB reads/writes go through here.
 */

import { supabase } from '@/lib/supabase'

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
}

export interface SimRunRole {
  id: string
  sim_run_id: string
  character_name: string
  country_id: string
  title: string
  is_head_of_state: boolean
  is_military_chief: boolean
  is_ai_operated: boolean
  is_economy_officer: boolean
  expansion_role: boolean
  powers: string[]
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

export async function createSimRun(params: {
  name: string
  template_id: string
  facilitator_id: string
  schedule: Record<string, number>
  key_events: unknown[]
  max_rounds: number
  human_participants: number
  ai_participants: number
  logo_url?: string
  description?: string
}): Promise<SimRun> {
  const { data, error } = await supabase
    .from('sim_runs')
    .insert({
      name: params.name,
      template_id: params.template_id,
      facilitator_id: params.facilitator_id,
      status: 'setup',
      current_round: 0,
      current_phase: 'pre',
      schedule: params.schedule,
      key_events: params.key_events,
      max_rounds: params.max_rounds,
      human_participants: params.human_participants,
      ai_participants: params.ai_participants,
      logo_url: params.logo_url ?? null,
      description: params.description ?? null,
      run_config: {},
    })
    .select()
    .single()

  if (error) throw error
  return data as SimRun
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

  const { data, error } = await supabase
    .from('sim_runs')
    .insert({
      name: newName,
      template_id: source.template_id,
      facilitator_id: source.facilitator_id,
      status: 'setup',
      current_round: 0,
      current_phase: 'pre',
      schedule: source.schedule,
      key_events: source.key_events,
      max_rounds: source.max_rounds,
      human_participants: source.human_participants,
      ai_participants: source.ai_participants,
      logo_url: source.logo_url,
      description: source.description,
      run_config: {},
    })
    .select()
    .single()

  if (error) throw error
  return data as SimRun
}

/* -------------------------------------------------------------------------- */
/*  Roles (per SimRun)                                                        */
/* -------------------------------------------------------------------------- */

export async function getSimRunRoles(simRunId: string): Promise<SimRunRole[]> {
  const { data, error } = await supabase
    .from('roles')
    .select('id, sim_run_id, character_name, country_id, title, is_head_of_state, is_military_chief, is_ai_operated, is_economy_officer, expansion_role, powers, status, user_id')
    .eq('sim_run_id', simRunId)
    .order('country_id')

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
  political_support: number
  dem_rep_split_dem: number
  dem_rep_split_rep: number
  war_tiredness: number
  nuclear_level: number
  nuclear_rd_progress: number
  ai_level: number
  ai_rd_progress: number
  home_zones: string
  country_brief: string | null
}

export interface Role {
  id: string
  sim_run_id: string
  character_name: string
  parallel: string
  country_id: string
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
  position_type: string
  party: string
  intelligence_pool: number
  sabotage_cards: number
  cyber_cards: number
  disinfo_cards: number
  election_meddling_cards: number
  assassination_cards: number
  protest_stim_cards: number
  fatherland_appeal: number
  powers: string[]
  objectives: string[]
  ticking_clock: string
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
  country_id: string
  org_id: string
  role_id: string | null
  role_in_org: string
  has_veto: boolean
  seat_type: string
}

export interface Relationship {
  id: string
  sim_run_id: string
  from_country_id: string
  to_country_id: string
  relationship: string
  status: string
  dynamic: string
  basing_rights_a_to_b: boolean
  basing_rights_b_to_a: boolean
}

export interface Sanction {
  id: string
  sim_run_id: string
  imposer_country_id: string
  target_country_id: string
  level: number
  notes: string
}

export interface Tariff {
  id: string
  sim_run_id: string
  imposer_country_id: string
  target_country_id: string
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
  country_id: string
  unit_type: string
  count: number
  zone_id: string
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
    .order('country_id, character_name')
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

export async function createRole(role: Partial<Role> & { id: string; character_name: string; country_id: string }): Promise<void> {
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
    .order('from_country_id, to_country_id')
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
    .order('imposer_country_id, target_country_id')
  if (error) throw error
  return (data ?? []) as Sanction[]
}

export async function getTemplateTariffs(): Promise<Tariff[]> {
  const { data, error } = await supabase
    .from('tariffs')
    .select('*')
    .eq('sim_run_id', DEFAULT_SIM_RUN_ID)
    .order('imposer_country_id, target_country_id')
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
    .order('country_id, zone_id, unit_type')
  if (error) throw error
  return (data ?? []) as Deployment[]
}
