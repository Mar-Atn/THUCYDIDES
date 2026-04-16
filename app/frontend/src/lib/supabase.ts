/**
 * Supabase client — singleton, persisted across Vite HMR.
 *
 * The client is stored on `window` so that hot module replacement
 * reuses the same instance instead of creating a new one.
 * This prevents auth lock contention and session loss during dev.
 */

import { createClient, type SupabaseClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL as string
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY as string

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error(
    'Missing VITE_SUPABASE_URL or VITE_SUPABASE_ANON_KEY. Check .env file.'
  )
}

// Persist across HMR — same pattern used in production apps with Vite
const GLOBAL_KEY = '__ttt_supabase_client__'

function getOrCreateClient(): SupabaseClient {
  const existing = (window as Record<string, unknown>)[GLOBAL_KEY] as SupabaseClient | undefined
  if (existing) return existing

  const client = createClient(supabaseUrl, supabaseAnonKey, {
    auth: {
      autoRefreshToken: true,
      persistSession: true,
      detectSessionInUrl: true,
    },
    realtime: {
      params: {
        eventsPerSecond: 10,
      },
    },
  })

  ;(window as Record<string, unknown>)[GLOBAL_KEY] = client
  return client
}

export const supabase = getOrCreateClient()
