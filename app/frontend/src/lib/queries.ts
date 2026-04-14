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
    .select('id, sim_run_id, character_name, country_id, title, is_head_of_state, is_military_chief, is_ai_operated, expansion_role, powers, status, user_id')
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
