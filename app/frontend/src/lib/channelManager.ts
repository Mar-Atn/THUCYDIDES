/**
 * ChannelManager — deduplicated Supabase Realtime channel manager.
 *
 * Part of the communication layer (lib/), NOT a UI concern.
 * Sits alongside supabase.ts as the infrastructure for all realtime subscriptions.
 *
 * Architecture:
 * - Singleton, persisted across HMR via window global
 * - Deduplicates channels by canonical key (table+simId)
 * - Reference-counts subscribers: channel removed when last listener unsubscribes
 * - Fans out Postgres Changes events to all registered listeners
 *
 * Designed for 30+ concurrent users × multiple browser tabs × 5+ hooks each.
 * Without deduplication, each hook × each HMR reload creates a new channel,
 * quickly exhausting the browser's HTTP/2 stream limit (ERR_INSUFFICIENT_RESOURCES).
 *
 * M2 Realtime Architecture (SPEC_M2_REALTIME.md)
 */

import { supabase } from '@/lib/supabase'
import type { RealtimeChannel } from '@supabase/supabase-js'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type RealtimeListener = (payload: {
  eventType: string
  new: Record<string, unknown>
  old: Record<string, unknown>
}) => void

interface ManagedChannel {
  channel: RealtimeChannel
  refCount: number
  listeners: Set<RealtimeListener>
  /** Config needed to recreate the channel on reconnect */
  config: ChannelConfig
  retryCount: number
  retryTimer: ReturnType<typeof setTimeout> | null
}

interface ChannelConfig {
  type: 'table' | 'row'
  table: string
  filterKey: string   // simId or rowId
}

/** Callback registered by hooks to re-fetch data on reconnect/visibility change */
export type RefetchCallback = () => void

// ---------------------------------------------------------------------------
// ChannelManager class
// ---------------------------------------------------------------------------

const GLOBAL_CM_KEY = '__ttt_channel_manager__'

class ChannelManager {
  private channels = new Map<string, ManagedChannel>()
  private refetchCallbacks = new Set<RefetchCallback>()

  private static readonly MAX_RETRIES = 5
  private static readonly BASE_DELAY_MS = 2000

  // -------------------------------------------------------------------------
  // Refetch registry — hooks register callbacks for forceRefreshAll
  // -------------------------------------------------------------------------

  /** Register a refetch callback (called by useRealtimeTable on mount). */
  registerRefetch(cb: RefetchCallback): void {
    this.refetchCallbacks.add(cb)
  }

  /** Unregister a refetch callback (called by useRealtimeTable on unmount). */
  unregisterRefetch(cb: RefetchCallback): void {
    this.refetchCallbacks.delete(cb)
  }

  /** Force all active hooks to re-fetch their data (e.g., after tab becomes visible). */
  forceRefreshAll(): void {
    for (const cb of this.refetchCallbacks) {
      try { cb() } catch { /* don't let one hook break others */ }
    }
  }

  // -------------------------------------------------------------------------
  // Reconnect logic
  // -------------------------------------------------------------------------

  /**
   * Handle channel error — exponential backoff reconnect.
   * Tears down the dead channel and recreates it with same config + listeners.
   */
  private handleChannelError(key: string): void {
    const managed = this.channels.get(key)
    if (!managed) return

    if (managed.retryCount >= ChannelManager.MAX_RETRIES) {
      console.error(`[ChannelManager] ${key}: giving up after ${ChannelManager.MAX_RETRIES} retries`)
      return
    }

    // Don't double-schedule
    if (managed.retryTimer) return

    managed.retryCount++
    const delay = ChannelManager.BASE_DELAY_MS * Math.min(managed.retryCount, 5)
    console.warn(`[ChannelManager] ${key}: reconnecting in ${delay}ms (attempt ${managed.retryCount})`)

    managed.retryTimer = setTimeout(() => {
      const current = this.channels.get(key)
      if (!current) return
      current.retryTimer = null

      // Tear down dead channel
      supabase.removeChannel(current.channel)

      // Recreate with same config
      const newChannel = this.createChannel(key, current.config)
      current.channel = newChannel

      // Re-subscribe
      newChannel.subscribe((status) => {
        if (status === 'SUBSCRIBED') {
          console.info(`[ChannelManager] ${key}: reconnected`)
          current.retryCount = 0
          // Trigger refetch on all hooks so they pick up missed events
          this.forceRefreshAll()
        }
        if (status === 'CHANNEL_ERROR' || status === 'TIMED_OUT') {
          console.warn(`[ChannelManager] ${key}: ${status} (reconnect attempt)`)
          this.handleChannelError(key)
        }
      })
    }, delay)
  }

  /**
   * Create a RealtimeChannel (without subscribing) for the given config.
   * Wires up the postgres_changes listener that fans out to all registered listeners.
   */
  private createChannel(key: string, config: ChannelConfig): RealtimeChannel {
    const event = config.type === 'row' ? 'UPDATE' : '*'
    const filterCol = config.type === 'row' ? 'id' : 'sim_run_id'
    const filterValue = config.filterKey

    return supabase
      .channel(key)
      .on(
        'postgres_changes',
        {
          event,
          schema: 'public',
          table: config.table,
          filter: `${filterCol}=eq.${filterValue}`,
        },
        (payload) => {
          const m = this.channels.get(key)
          if (!m) return
          for (const fn of m.listeners) {
            try {
              fn(payload as unknown as Parameters<RealtimeListener>[0])
            } catch {
              /* individual listener errors must not break others */
            }
          }
        },
      )
  }

  // -------------------------------------------------------------------------
  // Subscribe / unsubscribe (table)
  // -------------------------------------------------------------------------

  /**
   * Subscribe to Postgres Changes on a table filtered by sim_run_id.
   * Returns the canonical channel key for later unsubscribe().
   *
   * If a channel for this table+simId already exists, the listener is added
   * to the existing channel (ref count bumped). No new WebSocket/HTTP created.
   */
  subscribe(table: string, simId: string, listener: RealtimeListener): string {
    const key = `rt:${table}:${simId}`
    let managed = this.channels.get(key)

    if (managed) {
      managed.refCount++
      managed.listeners.add(listener)
      return key
    }

    const config: ChannelConfig = { type: 'table', table, filterKey: simId }
    const channel = this.createChannel(key, config)

    channel.subscribe((status) => {
      if (status === 'CHANNEL_ERROR' || status === 'TIMED_OUT') {
        console.warn(`[ChannelManager] ${key}: ${status}`)
        this.handleChannelError(key)
      }
    })

    managed = {
      channel, refCount: 1, listeners: new Set([listener]),
      config, retryCount: 0, retryTimer: null,
    }
    this.channels.set(key, managed)
    return key
  }

  /**
   * Unsubscribe a listener. When the last listener leaves, the channel is removed.
   */
  unsubscribe(key: string, listener: RealtimeListener): void {
    const managed = this.channels.get(key)
    if (!managed) return

    managed.listeners.delete(listener)
    managed.refCount--

    if (managed.refCount <= 0) {
      if (managed.retryTimer) clearTimeout(managed.retryTimer)
      supabase.removeChannel(managed.channel)
      this.channels.delete(key)
    }
  }

  // -------------------------------------------------------------------------
  // Subscribe / unsubscribe (row)
  // -------------------------------------------------------------------------

  /**
   * Subscribe to a single row by primary key (id column).
   * Same deduplication / ref-counting as subscribe(), but filters on id=eq.{rowId}.
   */
  subscribeRow(table: string, rowId: string, listener: RealtimeListener): string {
    const key = `rt:${table}:row:${rowId}`
    let managed = this.channels.get(key)

    if (managed) {
      managed.refCount++
      managed.listeners.add(listener)
      return key
    }

    const config: ChannelConfig = { type: 'row', table, filterKey: rowId }
    const channel = this.createChannel(key, config)

    channel.subscribe((status) => {
      if (status === 'CHANNEL_ERROR' || status === 'TIMED_OUT') {
        console.warn(`[ChannelManager] ${key}: ${status}`)
        this.handleChannelError(key)
      }
    })

    managed = {
      channel, refCount: 1, listeners: new Set([listener]),
      config, retryCount: 0, retryTimer: null,
    }
    this.channels.set(key, managed)
    return key
  }

  // -------------------------------------------------------------------------
  // Debug
  // -------------------------------------------------------------------------

  /** Number of active channels (for debugging). */
  get activeChannels(): number {
    return this.channels.size
  }

  /** Debug dump of all channels and their ref counts. */
  dump(): Record<string, number> {
    const out: Record<string, number> = {}
    for (const [key, managed] of this.channels) {
      out[key] = managed.refCount
    }
    return out
  }
}

// ---------------------------------------------------------------------------
// Singleton — persists across HMR
// ---------------------------------------------------------------------------

function getChannelManager(): ChannelManager {
  const w = window as Record<string, unknown>
  if (!w[GLOBAL_CM_KEY]) {
    w[GLOBAL_CM_KEY] = new ChannelManager()
  }
  return w[GLOBAL_CM_KEY] as ChannelManager
}

export const channelManager = getChannelManager()
