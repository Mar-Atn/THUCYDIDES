/**
 * ElevenLabs API client — fetches voice agents via backend proxy.
 *
 * The backend proxy at /api/elevenlabs/agents keeps the API key server-side.
 * Used by TabRoles.tsx and AIParticipantDashboard.tsx for voice agent assignment.
 */

import { supabase } from '@/lib/supabase'

/** Engine API base URL. Empty in dev (Vite proxy), set via VITE_API_URL in production. */
const API_BASE = import.meta.env.VITE_API_URL ?? ''

export interface ElevenLabsAgent {
  agent_id: string
  name: string
}

/**
 * Fetch available ElevenLabs conversational AI agents.
 *
 * Calls backend proxy which adds the API key server-side.
 * Requires moderator auth.
 */
export async function fetchElevenLabsAgents(): Promise<ElevenLabsAgent[]> {
  const { data: { session } } = await supabase.auth.getSession()
  const token = session?.access_token
  if (!token) throw new Error('Not authenticated')

  const resp = await fetch(`${API_BASE}/api/elevenlabs/agents`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  })

  if (!resp.ok) {
    const text = await resp.text()
    throw new Error(`Failed to fetch voice agents: ${resp.status} ${text}`)
  }

  const json = await resp.json()
  // Backend returns APIResponse format: {data: {agents: [...]}}
  return json.data?.agents || json.data || []
}
