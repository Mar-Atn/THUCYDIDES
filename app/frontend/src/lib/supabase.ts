/**
 * Supabase client — singleton, persisted across HMR.
 *
 * Navigator lock disabled to prevent "lock stolen" errors on page reload.
 * Client is stored on window to survive Vite HMR module reloads.
 */

import { createClient, type SupabaseClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL as string
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY as string

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error(
    'Missing VITE_SUPABASE_URL or VITE_SUPABASE_ANON_KEY. Check .env file.'
  )
}

// Version key — bump when client config changes to force re-creation
const GLOBAL_KEY = '__ttt_supabase_client_v3__'

function getOrCreateClient(): SupabaseClient {
  const w = window as Record<string, unknown>
  if (w[GLOBAL_KEY]) return w[GLOBAL_KEY] as SupabaseClient

  const client = createClient(supabaseUrl, supabaseAnonKey, {
    auth: {
      autoRefreshToken: true,
      persistSession: true,
      detectSessionInUrl: true,
      lock: async (_name: string, _acquireTimeout: number, fn: () => Promise<unknown>) => {
        return await fn()
      },
    },
    realtime: {
      params: {
        eventsPerSecond: 10,
      },
    },
  })

  w[GLOBAL_KEY] = client
  return client
}

export const supabase = getOrCreateClient()
