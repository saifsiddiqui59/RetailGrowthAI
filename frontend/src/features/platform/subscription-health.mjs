// No billing, invoice or renewal claims: only loaded server-authorized directory rows.
const WEEK_MS = 7 * 86400000
function expiryMillis(date) {
  if (typeof date !== 'string' || !date) return null
  const time = Date.parse(date)
  return Number.isFinite(time) ? time : null
}
export function classifySubscription(shop, now = Date.now()) {
  const state = typeof shop?.subscription_status === 'string' ? shop.subscription_status.toUpperCase() : ''
  const expiry = expiryMillis(shop?.valid_until)
  if (state === 'SUSPENDED') return 'suspended'
  if (state === 'EXPIRED' || expiry !== null && expiry <= now) return 'expired'
  if (expiry !== null && expiry > now && expiry <= now + WEEK_MS) return 'expiring'
  if (!state || expiry === null) return 'unknown'
  return 'healthy'
}
export function buildSubscriptionHealth(shops, now = Date.now()) {
  if (!Array.isArray(shops)) throw new Error('Subscription listing unavailable')
  const rows = shops.map(shop => ({
    id: shop.shop_id,
    name: shop.name,
    slug: shop.slug,
    plan: shop.plan_code ?? 'Unknown',
    validUntil: shop.valid_until ?? null,
    status: classifySubscription(shop, now),
    original: shop,
  }))
  return {
    rows,
    suspended: rows.filter(x=>x.status==='suspended').length,
    expired: rows.filter(x=>x.status==='expired').length,
    expiring: rows.filter(x=>x.status==='expiring').length,
    unknown: rows.filter(x=>x.status==='unknown').length,
  }
}
export function filterSubscriptionHealth(rows, status = 'all', search = '') {
  const q = String(search).trim().toLowerCase()
  return rows.filter(row => (status==='all' || row.status===status) &&
    (!q || [row.name,row.slug,row.plan].some(v => String(v||'').toLowerCase().includes(q))))
}
