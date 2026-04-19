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
}

// ---------------------------------------------------------------------------
// ChannelManager class
// ---------------------------------------------------------------------------

const GLOBAL_CM_KEY = '__ttt_channel_manager__'

class ChannelManager {
  private channels = new Map<string, ManagedChannel>()

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
      .subscribe((status) => {
        if (status === 'CHANNEL_ERROR' || status === 'TIMED_OUT') {
          console.warn(`[ChannelManager] ${key}: ${status}`)
        }
      })

    managed = { channel, refCount: 1, listeners: new Set([listener]) }
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
      supabase.removeChannel(managed.channel)
      this.channels.delete(key)
    }
  }

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
