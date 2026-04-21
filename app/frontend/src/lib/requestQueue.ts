/**
 * RequestQueue — concurrency-limited fetch queue for Supabase REST calls.
 *
 * Prevents ERR_INSUFFICIENT_RESOURCES by limiting simultaneous HTTP/2 streams.
 * Without this, 20+ useRealtimeTable hooks all fire initial fetches at once,
 * exhausting the browser's per-origin stream limit (~100 in Chrome).
 *
 * Fix (2026-04-21): drain() now fires ONE queued job per call instead of a
 * tight sync loop. Each completed job triggers the next via finally → drain().
 * This prevents the running counter from desyncing with actual in-flight work.
 */

const MAX_CONCURRENT = 12
const REQUEST_TIMEOUT_MS = 10000

class RequestQueue {
  private running = 0
  private queue: Array<{ run: () => Promise<void> }> = []

  async enqueue<T>(fn: () => Promise<T>): Promise<T> {
    if (this.running < MAX_CONCURRENT) {
      return this.execute(fn)
    }
    return new Promise<T>((resolve, reject) => {
      this.queue.push({
        run: async () => {
          try {
            resolve(await this.execute(fn))
          } catch (e) {
            reject(e)
          }
        },
      })
    })
  }

  private async execute<T>(fn: () => Promise<T>): Promise<T> {
    this.running++
    try {
      const result = await Promise.race([
        fn(),
        new Promise<never>((_, reject) =>
          setTimeout(() => reject(new Error('RequestQueue timeout')), REQUEST_TIMEOUT_MS)
        ),
      ])
      return result
    } catch (e) {
      // On timeout or error, still free the slot
      throw e
    } finally {
      this.running--
      // Drain ONE item — not a loop. The next drain() is triggered
      // by that item's own finally block, creating a proper chain.
      this.drainOne()
    }
  }

  private drainOne(): void {
    if (this.queue.length > 0 && this.running < MAX_CONCURRENT) {
      const next = this.queue.shift()
      if (next) next.run() // Single fire-and-forget is safe — it calls execute() which calls drainOne() on completion
    }
  }

  /** Reset the queue — call on navigation to prevent stale state. */
  reset(): void {
    this.queue = []
    // Don't reset running — in-flight requests will decrement naturally
  }
}

// Singleton — bump version key to force fresh instance after code changes
const GLOBAL_KEY = '__ttt_request_queue_v3__'
function getRequestQueue(): RequestQueue {
  const w = window as Record<string, unknown>
  // Clear old versions
  delete w['__ttt_request_queue__']
  delete w['__ttt_request_queue_v2__']
  if (!w[GLOBAL_KEY]) {
    w[GLOBAL_KEY] = new RequestQueue()
  }
  return w[GLOBAL_KEY] as RequestQueue
}

export const requestQueue = getRequestQueue()
