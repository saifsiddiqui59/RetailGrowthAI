// Read-only, tenant-scoped recovery for an already accepted F2 -> F4 CPU job.
// The only mutation is a deliberate, separate retailer POST; this module
// never retries it or persists signed URLs, JWTs, or any service credentials.
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/
const STATES = new Set(['QUEUED', 'RUNNING', 'SUCCEEDED', 'FAILED'])

function canonicalId(value) {
  if (typeof value !== 'string' || !UUID.test(value)) {
    throw Error('Verified private video resource ID required')
  }
  return value
}

export async function readFeature4CpuJobForPlan({
  shopId, planId, supabaseUrl, publishableKey, tokenProvider,
  fetchImpl = fetch,
}) {
  const shop = canonicalId(shopId)
  const plan = canonicalId(planId)
  let origin
  try {
    const parsed = new URL(supabaseUrl)
    if (parsed.protocol !== 'https:' || parsed.username || parsed.password ||
        parsed.pathname !== '/' || parsed.search || parsed.hash) throw Error()
    origin = parsed.origin
  } catch { throw Error('Private job history requires the configured HTTPS Supabase origin') }
  if (typeof publishableKey !== 'string' || !publishableKey ||
      /[\s\r\n]/.test(publishableKey) ||
      typeof tokenProvider !== 'function' || typeof fetchImpl !== 'function') {
    throw Error('Authenticated private job history is unavailable')
  }
  const token = await tokenProvider()
  if (typeof token !== 'string' || token.length < 10 ||
      /[\s\r\n]/.test(token)) throw Error('Current retailer sign-in required')
  const url = new URL('/rest/v1/feature4_cpu_render_jobs', origin)
  url.searchParams.set('select', 'id,shop_id,plan_id,status')
  url.searchParams.set('shop_id', 'eq.' + shop)
  url.searchParams.set('plan_id', 'eq.' + plan)
  url.searchParams.set('limit', '2')
  const response = await fetchImpl(url.toString(), {
    method: 'GET', redirect: 'error', cache: 'no-store',
    headers: { apikey: publishableKey, Authorization: 'Bearer ' + token },
  })
  if (!response?.ok) throw Error('Private render history could not be verified')
  const rows = await response.json().catch(() => null)
  if (!Array.isArray(rows) || rows.length > 1) {
    throw Error('Ambiguous private render history response')
  }
  if (rows.length === 0) return null
  const row = rows[0]
  if (!row || typeof row !== 'object' || Array.isArray(row) ||
      row.shop_id !== shop || row.plan_id !== plan ||
      !UUID.test(row.id) || !STATES.has(row.status)) {
    throw Error('Private render history failed tenant/plan verification')
  }
  return Object.freeze({ id: row.id, shop_id: shop,
    plan_id: plan, status: row.status })
}
