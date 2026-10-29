/** Strict tenant-private generated GPU job metadata; never accepts URLs.
 * Browser GET history can be displayed without generating, charging, signing
 * a Storage URL, or marking an unreviewed image customer/publish-approved.
 */
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/
const STATES = new Set(['QUEUED','RUNNING','SUCCEEDED','FAILED'])
const ROW_KEYS = ['id','shop_id','status']
const empty = shopId => Object.freeze({
  shopId, jobs: Object.freeze([]), message: '', busy: false,
})

export function validateFeature3GeneratedHistory(shopId, jobs) {
  if (!UUID.test(shopId || '') || !Array.isArray(jobs) || jobs.length > 20)
    throw Error('Invalid private generated job scope')
  const unique = new Set()
  const checked = []
  for (const row of jobs) {
    if (!row || typeof row !== 'object' || Array.isArray(row) ||
        Object.keys(row).length !== ROW_KEYS.length ||
        ROW_KEYS.some(key => !Object.hasOwn(row,key)) ||
        row.shop_id !== shopId || !UUID.test(row.id) ||
        !STATES.has(row.status) || unique.has(row.id)) {
      throw Error('Untrusted private generated image job row')
    }
    unique.add(row.id)
    checked.push(Object.freeze({id:row.id,shop_id:shopId,status:row.status}))
  }
  return Object.freeze(checked)
}

export function scopedFeature3GeneratedHistory(value, shopId) {
  if (!UUID.test(shopId || '') || !value || value.shopId !== shopId ||
      !Array.isArray(value.jobs)) return empty(shopId)
  try {
    // Never propagate arbitrary caller state (URLs, tokens, approval hints,
    // private object keys) into a tenant-visible history snapshot.
    return Object.freeze({
      shopId,
      jobs:validateFeature3GeneratedHistory(shopId,value.jobs),
      message:typeof value.message === 'string' && value.message.length <= 300
        ? value.message : '',
      busy:value.busy === true,
    })
  } catch {
    return empty(shopId)
  }
}

/** Local-only status view; never asks the API for more data or keeps media. */
export const FEATURE3_HISTORY_FILTERS = Object.freeze([
  'ALL', 'QUEUED', 'RUNNING', 'SUCCEEDED', 'FAILED',
])

export function filteredFeature3GeneratedHistory(shopId, jobs, status = 'ALL') {
  if (!FEATURE3_HISTORY_FILTERS.includes(status)) {
    throw Error('Unknown generated-image history filter')
  }
  const safe = validateFeature3GeneratedHistory(shopId, jobs)
  return status === 'ALL' ? safe : Object.freeze(
    safe.filter(row => row.status === status))
}
