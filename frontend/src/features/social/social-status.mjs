// Client-side presentation only. The server and RLS authorize every job.
const STATES = new Set(['DRAFT','APPROVED','QUEUED','SENDING',
  'PROCESSING','PUBLISHED','RETRYABLE','RECONCILE','FAILED','CANCELED'])
const SAFE_CODE = /^[A-Z][A-Z0-9_]{0,63}$/

export function socialStatusForShop(jobs, shopId) {
  const counts = Object.fromEntries([...STATES].map(state => [state, 0]))
  const attention = []
  if (!Array.isArray(jobs) || typeof shopId !== 'string' || !shopId) {
    return { counts, attention, total: 0 }
  }
  for (const job of jobs) {
    if (!job || job.shop_id !== shopId || !STATES.has(job.status)) continue
    counts[job.status]++
    if (job.status === 'RECONCILE' || job.status === 'FAILED') {
      attention.push({
        id: job.id,
        provider: ['facebook','instagram','linkedin','youtube'].includes(job.provider)
          ? job.provider : 'social',
        status: job.status,
        code: typeof job.last_error_code === 'string' &&
          SAFE_CODE.test(job.last_error_code) ? job.last_error_code : null,
      })
    }
  }
  return { counts, attention: attention.slice(0, 20),
    total: Object.values(counts).reduce((sum, n) => sum + n, 0) }
}
