/**
 * realtimeHealth — visibility change handler + heartbeat for Realtime resilience.
 *
 * Handles two scenarios where WebSocket connections silently die:
 * 1. Tab switch (especially Safari/iOS) — visibilitychange triggers refetch
 * 2. Long idle — 30s heartbeat detects stale connections
 *
 * Depends on channelManager.forceRefreshAll() to trigger data re-fetch
 * across all active useRealtimeTable / useRealtimeRow hooks.
 *
 * Auto-initializes on import. Call cleanup() only if you need to tear down
 * (e.g., in tests).
 */

import { channelManager } from '@/lib/channelManager'

let visibilityHandler: (() => void) | null = null
let heartbeatInterval: ReturnType<typeof setInterval> | null = null

const HEARTBEAT_INTERVAL_MS = 30_000

function init(): void {
  // Guard against double-init (HMR, multiple imports)
  if (visibilityHandler) return

  // 1. Visibility change — tab became visible after being hidden
  visibilityHandler = () => {
    if (document.visibilityState === 'visible') {
      channelManager.forceRefreshAll()
    }
  }
  document.addEventListener('visibilitychange', visibilityHandler)

  // 2. Heartbeat — periodic check. Channels that have silently died
  //    will get CHANNEL_ERROR on next message attempt; the reconnect
  //    logic in channelManager handles recovery. The heartbeat's main
  //    job is to trigger a refetch so stale data doesn't sit unnoticed.
  heartbeatInterval = setInterval(() => {
    if (document.visibilityState === 'visible') {
      channelManager.forceRefreshAll()
    }
  }, HEARTBEAT_INTERVAL_MS)
}

/** Tear down listeners (for tests or cleanup). */
export function cleanup(): void {
  if (visibilityHandler) {
    document.removeEventListener('visibilitychange', visibilityHandler)
    visibilityHandler = null
  }
  if (heartbeatInterval) {
    clearInterval(heartbeatInterval)
    heartbeatInterval = null
  }
}

// Auto-initialize
init()
