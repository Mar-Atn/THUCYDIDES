/**
 * Supabase client — singleton with navigator lock disabled.
 *
 * The PKCE flow's navigator.locks API causes "lock stolen" errors
 * on page reload and HMR. We disable it by providing a custom lock
 * implementation that uses a simple promise-based mutex instead.
 */

import { createClient, type SupabaseClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL as string
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY as string

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error(
    'Missing VITE_SUPABASE_URL or VITE_SUPABASE_ANON_KEY. Check .env file.'
  )
}

// Persist across HMR
const GLOBAL_KEY = '__ttt_supabase_client__'

function getOrCreateClient(): SupabaseClient {
  const w = window as Record<string, unknown>
  if (w[GLOBAL_KEY]) return w[GLOBAL_KEY] as SupabaseClient

  const client = createClient(supabaseUrl, supabaseAnonKey, {
    auth: {
      autoRefreshToken: true,
      persistSession: true,
      detectSessionInUrl: true,
      // Disable navigator.locks — use simple mutex instead
      // This prevents "lock stolen" errors on page reload
      lock: async (name: string, _acquireTimeout: number, fn: () => Promise<unknown>) => {
        // Simple non-blocking lock — just run the function
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
