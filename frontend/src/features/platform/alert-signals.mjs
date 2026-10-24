// Read-only, derived operator signals from already-authorized platform RPC snapshots.
// No durable notification history or sender/delivery state is implied.
const DAY = 86400000
const isoMillis = (value) => {
  if (typeof value !== 'string' || !value) return null
  const time = Date.parse(value)
  return Number.isFinite(time) ? time : null
}

export function derivePlatformAlerts({ summary, requests, listing, now = Date.now() }) {
  if (!summary || !Number.isSafeInteger(summary.expired_or_suspended) ||
      !Number.isSafeInteger(summary.retailers) || !Array.isArray(requests) ||
      !listing || !Array.isArray(listing.shops) ||
      !Number.isSafeInteger(listing.total) || listing.total < listing.shops.length) {
    throw new Error('Platform monitoring response is unavailable')
  }
  const items = []
  for (const request of requests) {
    if (request?.status !== 'PENDING' || typeof request.user_id !== 'string' ||
        typeof request.email !== 'string') continue
    items.push({
      id: 'signup:' + request.user_id, level: 'action', category: 'Onboarding',
      title: 'Retailer waiting for approval',
      detail: request.email, destination: '/platform-admin',
      action: 'Review retailer', date: isoMillis(request.requested_at),
    })
  }
  if (summary.expired_or_suspended > 0) items.push({
    id: 'aggregate:expired', level: 'action', category: 'Subscriptions',
    title: summary.expired_or_suspended + ' expired or suspended entitlements',
    detail: 'Verified platform-wide count; check retailer subscriptions before changes.',
    destination: '/platform-admin', action: 'Inspect plans', date: null,
  })
  for (const shop of listing.shops) {
    const expiry = isoMillis(shop?.valid_until)
    if (typeof shop?.shop_id !== 'string' || expiry === null) continue
    if (shop.subscription_status === 'SUSPENDED' || shop.subscription_status === 'EXPIRED') continue
    if (expiry > now && expiry <= now + 7 * DAY) items.push({
      id: 'expiry:' + shop.shop_id, level: 'attention', category: 'Subscriptions',
      title: 'Subscription due within 7 days',
      detail: shop.name + ' · expires ' + new Date(expiry).toLocaleDateString('en-IN'),
      destination: '/platform-admin', action: 'Inspect plan', date: expiry,
    })
  }
  if (listing.total > listing.shops.length) items.push({
    id: 'coverage:partial', level: 'info', category: 'Coverage',
    title: 'Subscription due-date scan is partial',
    detail: 'Only ' + listing.shops.length + ' of ' + listing.total +
      ' shops were scanned; platform-wide expired/suspended counts remain verified.',
    destination: '/platform-admin', action: 'Browse retailers', date: null,
  })
  items.push({
    id: 'integration:pending', level: 'info', category: 'Monitoring',
    title: 'Delivery and cloud failure alerts are not connected',
    detail: 'This page shows current authorized Supabase snapshots, not email delivery, Azure incidents, failed jobs or persistent inbox history.',
    destination: '/platform-admin', action: 'Open Platform Control', date: null,
  })
  const weight = {action:0,attention:1,info:2}
  return items.sort((a,b) => weight[a.level]-weight[b.level] || (b.date||0)-(a.date||0))
}
