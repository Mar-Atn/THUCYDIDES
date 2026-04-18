/**
 * useRealtimeTable — subscribe to a Supabase table with automatic updates.
 *
 * Handles: initial fetch, INSERT/UPDATE/DELETE via Postgres Changes,
 * reconnection with full re-fetch, cleanup on unmount.
 *
 * M2 Realtime Architecture (SPEC_M2_REALTIME.md)
 */

import { useEffect, useState, useRef, useCallback } from 'react'
import { supabase } from '@/lib/supabase'
import type { RealtimeChannel } from '@supabase/supabase-js'

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
  const channelRef = useRef<RealtimeChannel | null>(null)

  const fetchData = useCallback(async () => {
    if (!simId || !enabled) return
    let query = supabase.from(table).select(columns).eq('sim_run_id', simId)
    if (eq) {
      for (const [k, v] of Object.entries(eq)) {
        query = query.eq(k, v)
      }
    }
    if (filter) {
      // Parse simple filter like "status=eq.pending"
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

    // Subscribe to changes
    const channelName = `rt:${table}:${simId}:${filter || 'all'}:${JSON.stringify(eq || {})}`
    const channel = supabase
      .channel(channelName)
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: table,
          filter: `sim_run_id=eq.${simId}`,
        },
        (payload) => {
          const { eventType, new: newRow, old: oldRow } = payload

          setData((prev) => {
            if (eventType === 'INSERT') {
              const row = newRow as T
              // Check additional filters match
              if (filter) {
                const parts = filter.split('=')
                if (parts.length === 2) {
                  const [col, rest] = parts
                  const val = rest.split('.')[1]
                  if (String((row as Record<string, unknown>)[col]) !== val) return prev
                }
              }
              if (eq) {
                for (const [k, v] of Object.entries(eq)) {
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
              // Check if this row should be in our filtered set
              let matchesFilter = true
              if (filter) {
                const parts = filter.split('=')
                if (parts.length === 2) {
                  const [col, rest] = parts
                  const val = rest.split('.')[1]
                  if (String((row as Record<string, unknown>)[col]) !== val) matchesFilter = false
                }
              }
              if (eq) {
                for (const [k, v] of Object.entries(eq)) {
                  if (String((row as Record<string, unknown>)[k]) !== v) matchesFilter = false
                }
              }
              if (matchesFilter) {
                // Update existing or add if new match
                const exists = prev.some((r) => r[idField] === id)
                if (exists) return prev.map((r) => r[idField] === id ? row : r)
                return [row, ...prev]
              } else {
                // Remove if no longer matches filter
                return prev.filter((r) => r[idField] !== id)
              }
            }

            if (eventType === 'DELETE') {
              const id = (oldRow as Record<string, unknown>)?.[idField]
              if (id) return prev.filter((r) => r[idField] !== id)
              // If no old row (no REPLICA IDENTITY FULL), re-fetch
              fetchData()
              return prev
            }

            return prev
          })
        },
      )
      .subscribe((status) => {
        if (status === 'CHANNEL_ERROR' || status === 'TIMED_OUT') {
          // Reconnect with full re-fetch
          setTimeout(fetchData, 2000)
        }
      })

    channelRef.current = channel

    return () => {
      if (channelRef.current) {
        supabase.removeChannel(channelRef.current)
        channelRef.current = null
      }
    }
  }, [simId, table, filter, enabled, fetchData, idField, eq, limit])

  return { data, loading, refetch: fetchData }
}


/**
 * useRealtimeRow — subscribe to a single row by ID.
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

    // Subscribe
    const channel = supabase
      .channel(`rt:${table}:row:${id}`)
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
