/**
 * RequestQueue — concurrency-limited fetch queue for Supabase REST calls.
 *
 * Prevents ERR_INSUFFICIENT_RESOURCES by limiting simultaneous HTTP/2 streams.
 * Without this, 20+ useRealtimeTable hooks all fire initial fetches at once,
 * exhausting the browser's per-origin stream limit (~100 in Chrome).
 *
 * Usage: wrap any supabase query's .then() in requestQueue.enqueue():
 *   const result = await requestQueue.enqueue(() => supabase.from('t').select('*').execute())
 */

const MAX_CONCURRENT = 6

class RequestQueue {
  private running = 0
  private queue: Array<{ run: () => Promise<void> }> = []

  async enqueue<T>(fn: () => Promise<T>): Promise<T> {
    // If under limit, run immediately
    if (this.running < MAX_CONCURRENT) {
      return this.execute(fn)
    }
    // Otherwise, queue and wait
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
      return await fn()
    } finally {
      this.running--
      this.drain()
    }
  }

  private drain(): void {
    while (this.queue.length > 0 && this.running < MAX_CONCURRENT) {
      const next = this.queue.shift()
      if (next) next.run()
    }
  }
}

// Singleton — persisted across HMR via window global
const GLOBAL_KEY = '__ttt_request_queue__'
function getRequestQueue(): RequestQueue {
  const w = window as Record<string, unknown>
  if (!w[GLOBAL_KEY]) {
    w[GLOBAL_KEY] = new RequestQueue()
  }
  return w[GLOBAL_KEY] as RequestQueue
}

export const requestQueue = getRequestQueue()
