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
  if (!token) {
    console.warn('[elevenlabs] No auth session — cannot fetch agents')
    throw new Error('Not authenticated')
  }

  const url = `${API_BASE}/api/elevenlabs/agents`
  console.info('[elevenlabs] Fetching agents from', url)

  const resp = await fetch(url, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  })

  if (!resp.ok) {
    const text = await resp.text()
    console.error('[elevenlabs] Fetch failed:', resp.status, text)
    throw new Error(`Failed to fetch voice agents: ${resp.status} ${text}`)
  }

  const json = await resp.json()
  console.error('[elevenlabs] Raw response keys:', Object.keys(json))
  console.error('[elevenlabs] json.data type:', typeof json.data, Array.isArray(json.data) ? 'array' : '')
  console.error('[elevenlabs] json.data keys:', json.data ? Object.keys(json.data) : 'null')
  console.error('[elevenlabs] json.data.agents?:', json.data?.agents?.length ?? 'undefined')
  const agents = json.data?.agents || json.data || []
  console.error('[elevenlabs] Fetched', agents.length, 'agents')
  return agents
}
