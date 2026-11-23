// Read-only F2 -> F4 lost-ACK recovery. This uses the user's current JWT
// and the existing tenant RLS policy; it does not issue plans, render POSTs,
// approval clicks, service-role calls, credit reservations or signed media URLs.
import { canonicalVideoId } from './video-transport.mjs'

const SHA = /^[0-9a-f]{64}$/
const STATES = new Set(['QUEUED', 'RUNNING', 'SUCCEEDED', 'FAILED'])

export async function findFeature4CpuRenderJob({
  shopId, planId, reviewHash, supabaseOrigin, publishableKey, tokenProvider,
  fetchImpl = fetch,
}) {
  const shop = canonicalVideoId(shopId)
  const plan = canonicalVideoId(planId)
  if (typeof reviewHash !== 'string' || !SHA.test(reviewHash)) {
    throw Error('Current reviewed creative fingerprint required')
  }
  if (typeof tokenProvider !== 'function' || typeof fetchImpl !== 'function' ||
      typeof publishableKey !== 'string' || publishableKey.length < 12 ||
      /[\s\r\n]/.test(publishableKey)) {
    throw Error('Private Supabase reader is not configured')
  }
  let base
  try {
    const url = new URL(supabaseOrigin)
    if (url.protocol !== 'https:' || url.username || url.password ||
        url.pathname !== '/' || url.search || url.hash) throw Error()
    base = url.origin
  } catch { throw Error('A bare HTTPS private database origin is required') }

  const token = await tokenProvider()
  if (typeof token !== 'string' || token.length < 10 || /[\s\r\n]/.test(token)) {
    throw Error('Current business sign-in is required')
  }
  const url = new URL(base + '/rest/v1/feature4_cpu_render_jobs')
  url.searchParams.set('select',
    'id,shop_id,campaign_id,plan_id,approved_review_sha256,status')
  url.searchParams.set('shop_id', 'eq.' + shop)
  url.searchParams.set('plan_id', 'eq.' + plan)
  url.searchParams.set('limit', '2')
  const response = await fetchImpl(url.toString(), {
    method: 'GET', redirect: 'error', cache: 'no-store', credentials: 'omit',
    headers: { apikey: publishableKey, Authorization: 'Bearer ' + token },
  })
  if (!response || !response.ok) {
    throw Error('Existing private CPU render history unavailable')
  }
  const rows = await response.json().catch(() => null)
  if (!Array.isArray(rows) || rows.length > 1 || rows.some(row =>
    !row || row.shop_id !== shop || row.plan_id !== plan ||
    canonicalIdOrNull(row.id) === null ||
    canonicalIdOrNull(row.campaign_id) === null ||
    row.approved_review_sha256 !== reviewHash || !STATES.has(row.status))) {
    throw Error('Existing CPU job failed tenant, revision or status verification')
  }
  if (!rows.length) return null
  const job = rows[0]
  return { job_id: job.id, shop_id: shop, plan_id: plan,
    campaign_id: job.campaign_id, status: job.status }
}

function canonicalIdOrNull(value) {
  try { return canonicalVideoId(value) }
  catch { return null }
}
