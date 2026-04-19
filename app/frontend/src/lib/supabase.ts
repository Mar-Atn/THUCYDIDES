/**
 * Supabase client — singleton with connection management.
 *
 * Two critical features:
 * 1. Navigator lock disabled (prevents "lock stolen" errors on HMR)
 * 2. Throttled fetch: limits concurrent HTTP requests to Supabase REST API
 *    to prevent browser ERR_INSUFFICIENT_RESOURCES.
 *
 * The throttle is necessary because the app makes 50-70 REST calls per page
 * across mount effects and realtime hooks. With 4+ browser tabs, this
 * exceeds the browser's per-origin connection limit (~6 HTTP/1.1, ~100 HTTP/2).
 */

import { createClient, type SupabaseClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL as string
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY as string

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error(
    'Missing VITE_SUPABASE_URL or VITE_SUPABASE_ANON_KEY. Check .env file.'
  )
}

// ---------------------------------------------------------------------------
// Throttled fetch — limits concurrent requests to Supabase REST API
// ---------------------------------------------------------------------------

const MAX_CONCURRENT = 4  // max simultaneous REST requests per tab
const QUEUE_KEY = '__ttt_fetch_queue__'

interface FetchQueue {
  active: number
  queue: Array<{ resolve: (v: unknown) => void; args: [RequestInfo | URL, RequestInit?] }>
}

function getFetchQueue(): FetchQueue {
  const w = window as Record<string, unknown>
  if (!w[QUEUE_KEY]) {
    w[QUEUE_KEY] = { active: 0, queue: [] } as FetchQueue
  }
  return w[QUEUE_KEY] as FetchQueue
}

function processQueue(): void {
  const q = getFetchQueue()
  while (q.active < MAX_CONCURRENT && q.queue.length > 0) {
    const item = q.queue.shift()!
    q.active++
    window.fetch.apply(window, item.args as [RequestInfo | URL, RequestInit?])
      .then(
        (res) => { q.active--; item.resolve(res); processQueue() },
        (err) => { q.active--; item.resolve(Promise.reject(err)); processQueue() },
      )
  }
}

function throttledFetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  const q = getFetchQueue()

  // If under limit, execute immediately
  if (q.active < MAX_CONCURRENT) {
    q.active++
    return window.fetch(input, init).finally(() => {
      q.active--
      processQueue()
    })
  }

  // Otherwise queue it
  return new Promise((resolve) => {
    q.queue.push({ resolve, args: [input, init] })
  }) as Promise<Response>
}

// ---------------------------------------------------------------------------
// Client singleton — persists across HMR
// ---------------------------------------------------------------------------

// Version bump forces client re-creation when fetch strategy changes
const GLOBAL_KEY = '__ttt_supabase_client_v2__'

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
    global: {
      fetch: throttledFetch,
    },
  })

  w[GLOBAL_KEY] = client
  return client
}

export const supabase = getOrCreateClient()
