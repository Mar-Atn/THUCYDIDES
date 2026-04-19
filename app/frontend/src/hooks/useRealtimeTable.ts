/**
 * useRealtimeTable — subscribe to a Supabase table with automatic updates.
 *
 * Architecture: Global ChannelManager deduplicates Postgres Changes channels.
 * Multiple components subscribing to the same table+simId share ONE channel.
 * Reference-counted: channel is removed only when the last subscriber unmounts.
 *
 * This is critical for scalability — 30+ users × multiple tabs × 5 hooks each
 * would otherwise exhaust the browser connection pool and Supabase channel limit.
 *
 * M2 Realtime Architecture (SPEC_M2_REALTIME.md)
 */

import { useEffect, useState, useCallback, useRef } from 'react'
import { supabase } from '@/lib/supabase'
import type { RealtimeChannel } from '@supabase/supabase-js'

// ---------------------------------------------------------------------------
// ChannelManager — singleton, shared across all hooks, survives HMR
// ---------------------------------------------------------------------------

type Listener = (payload: { eventType: string; new: Record<string, unknown>; old: Record<string, unknown> }) => void

interface ManagedChannel {
  channel: RealtimeChannel
  refCount: number
  listeners: Set<Listener>
}

const GLOBAL_CM_KEY = '__ttt_channel_manager__'

class ChannelManager {
  private channels = new Map<string, ManagedChannel>()

  /** Get or create a Postgres Changes channel for table+simId. */
  subscribe(table: string, simId: string, listener: Listener): string {
    const key = `rt:${table}:${simId}`
    let managed = this.channels.get(key)

    if (managed) {
      // Reuse existing channel — just bump ref count
      managed.refCount++
      managed.listeners.add(listener)
      return key
    }

    // Create new channel
    const channel = supabase
      .channel(key)
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: table,
          filter: `sim_run_id=eq.${simId}`,
        },
        (payload) => {
          // Fan out to all listeners
          const m = this.channels.get(key)
          if (!m) return
          for (const fn of m.listeners) {
            try { fn(payload as unknown as Parameters<Listener>[0]) } catch { /* swallow */ }
          }
        },
      )
      .subscribe((status) => {
        if (status === 'CHANNEL_ERROR' || status === 'TIMED_OUT') {
          // On error, listeners will re-fetch on their own via reconnect logic
          console.warn(`[ChannelManager] ${key} error: ${status}`)
        }
      })

    managed = { channel, refCount: 1, listeners: new Set([listener]) }
    this.channels.set(key, managed)
    return key
  }

  /** Remove a listener. When refCount drops to 0, remove the channel. */
  unsubscribe(key: string, listener: Listener): void {
    const managed = this.channels.get(key)
    if (!managed) return

    managed.listeners.delete(listener)
    managed.refCount--

    if (managed.refCount <= 0) {
      supabase.removeChannel(managed.channel)
      this.channels.delete(key)
    }
  }

  /** Debug: how many active channels. */
  get size(): number { return this.channels.size }
}

// Persist across HMR
function getChannelManager(): ChannelManager {
  const w = window as Record<string, unknown>
  if (!w[GLOBAL_CM_KEY]) {
    w[GLOBAL_CM_KEY] = new ChannelManager()
  }
  return w[GLOBAL_CM_KEY] as ChannelManager
}

const channelManager = getChannelManager()

// ---------------------------------------------------------------------------
// useRealtimeTable hook
// ---------------------------------------------------------------------------

interface UseRealtimeTableOptions {
  columns?: string
  filter?: string           // PostgREST filter string e.g. "status=eq.pending"
  eq?: Record<string, string>  // additional eq filters
  orderBy?: string          // e.g. "created_at.desc"
  limit?: number
  enabled?: boolean         // set false to disable (default true)
  idField?: string          // primary key field name (default "id")
}

export function useRealtimeTable<T extends Record<string, unknown>>(
  table: string,
  simId: string | undefined,
  options: UseRealtimeTableOptions = {},
) {
  const {
    columns = '*',
    filter,
    eq,
    orderBy,
    limit,
    enabled = true,
    idField = 'id',
  } = options

  const [data, setData] = useState<T[]>([])
  const [loading, setLoading] = useState(true)

  // Stable references for filter/eq to avoid unnecessary re-subscriptions
  const filterRef = useRef(filter)
  const eqRef = useRef(eq)
  filterRef.current = filter
  eqRef.current = eq

  const fetchData = useCallback(async () => {
    if (!simId || !enabled) return
    let query = supabase.from(table).select(columns).eq('sim_run_id', simId)
    if (eq) {
      for (const [k, v] of Object.entries(eq)) {
        query = query.eq(k, v)
      }
    }
    if (filter) {
      const parts = filter.split('=')
      if (parts.length === 2) {
        const [col, rest] = parts
        const [op, val] = rest.split('.')
        if (op === 'eq') query = query.eq(col, val)
        else if (op === 'neq') query = query.neq(col, val)
      }
    }
    if (orderBy) {
      const [col, dir] = orderBy.split('.')
      query = query.order(col, { ascending: dir !== 'desc' })
    }
    if (limit) query = query.limit(limit)

    const { data: rows, error } = await query
    if (!error && rows) {
      setData(rows as T[])
    }
    setLoading(false)
  }, [table, simId, columns, filter, eq, orderBy, limit, enabled])

  useEffect(() => {
    if (!simId || !enabled) {
      setLoading(false)
      return
    }

    // Initial fetch
    fetchData()

    // Subscribe via ChannelManager (deduplicated per table+simId)
    const listener: Listener = (payload) => {
      const { eventType, new: newRow, old: oldRow } = payload

      setData((prev) => {
        if (eventType === 'INSERT') {
          const row = newRow as T
          // Check additional filters match
          if (filterRef.current) {
            const parts = filterRef.current.split('=')
            if (parts.length === 2) {
              const [col, rest] = parts
              const val = rest.split('.')[1]
              if (String((row as Record<string, unknown>)[col]) !== val) return prev
            }
          }
          if (eqRef.current) {
            for (const [k, v] of Object.entries(eqRef.current)) {
              if (String((row as Record<string, unknown>)[k]) !== v) return prev
            }
          }
          // Avoid duplicates
          const exists = prev.some((r) => r[idField] === (row as Record<string, unknown>)[idField])
          if (exists) return prev.map((r) => r[idField] === (row as Record<string, unknown>)[idField] ? row : r)
          const next = [row, ...prev]
          return limit ? next.slice(0, limit) : next
        }

        if (eventType === 'UPDATE') {
          const row = newRow as T
          const id = (row as Record<string, unknown>)[idField]
          let matchesFilter = true
          if (filterRef.current) {
            const parts = filterRef.current.split('=')
            if (parts.length === 2) {
              const [col, rest] = parts
              const val = rest.split('.')[1]
              if (String((row as Record<string, unknown>)[col]) !== val) matchesFilter = false
            }
          }
          if (eqRef.current) {
            for (const [k, v] of Object.entries(eqRef.current)) {
              if (String((row as Record<string, unknown>)[k]) !== v) matchesFilter = false
            }
          }
          if (matchesFilter) {
            const exists = prev.some((r) => r[idField] === id)
            if (exists) return prev.map((r) => r[idField] === id ? row : r)
            return [row, ...prev]
          } else {
            return prev.filter((r) => r[idField] !== id)
          }
        }

        if (eventType === 'DELETE') {
          const id = (oldRow as Record<string, unknown>)?.[idField]
          if (id) return prev.filter((r) => r[idField] !== id)
          fetchData()
          return prev
        }

        return prev
      })
    }

    const channelKey = channelManager.subscribe(table, simId, listener)

    return () => {
      channelManager.unsubscribe(channelKey, listener)
    }
  }, [simId, table, enabled, fetchData, idField, limit])

  return { data, loading, refetch: fetchData }
}


/**
 * useRealtimeRow — subscribe to a single row by ID.
 * Uses ChannelManager for deduplication (keyed by table+id).
 */
export function useRealtimeRow<T extends Record<string, unknown>>(
  table: string,
  id: string | undefined,
  columns: string = '*',
) {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!id) { setLoading(false); return }

    // Initial fetch
    supabase.from(table).select(columns).eq('id', id).limit(1)
      .then(({ data: rows }) => {
        if (rows?.[0]) setData(rows[0] as T)
        setLoading(false)
      })

    // Subscribe — use stable channel name (no random suffix)
    const channelName = `rt:${table}:row:${id}`

    // Check if channel already exists on the Supabase client
    const channel = supabase
      .channel(channelName)
      .on('postgres_changes', {
        event: 'UPDATE',
        schema: 'public',
        table: table,
        filter: `id=eq.${id}`,
      }, (payload) => {
        setData(payload.new as T)
      })
      .subscribe()

    return () => { supabase.removeChannel(channel) }
  }, [id, table, columns])

  return { data, loading }
}
