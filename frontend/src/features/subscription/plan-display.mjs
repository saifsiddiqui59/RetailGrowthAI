// Presentation-only limits matching the server-owned DEV SQL migration.
// They do NOT grant plans; subscriptions and quota reservations come from RLS.
export const PLAN_LIMITS = Object.freeze({
  TRIAL: Object.freeze({ campaign: 2, render: 2 }),
  STARTER: Object.freeze({ campaign: 15, render: 10 }),
  GROWTH: Object.freeze({ campaign: 60, render: 45 }),
  BUSINESS: Object.freeze({ campaign: 200, render: 150 }),
})

export function presentSubscription(subscription, usage, nowMs = Date.now()) {
  if (!subscription || !PLAN_LIMITS[subscription.plan_code]) {
    throw new Error('No recognized business subscription')
  }
  if (!usage || !Number.isSafeInteger(usage.campaign) || usage.campaign < 0 ||
      !Number.isSafeInteger(usage.render) || usage.render < 0) {
    throw new Error('Usage could not be verified')
  }
  const end = Date.parse(subscription.valid_until)
  const periodEnd = Date.parse(subscription.period_end)
  const periodStart = Date.parse(subscription.period_start)
  const begin = Date.parse(subscription.valid_from)
  if (![end, periodEnd, periodStart, begin, nowMs].every(Number.isFinite) ||
      begin >= end || periodStart >= periodEnd) {
    throw new Error('Invalid subscription dates')
  }
  const active = ['TRIAL', 'ACTIVE'].includes(subscription.status) &&
    nowMs >= begin && nowMs < end && nowMs >= periodStart && nowMs < periodEnd
  const limits = PLAN_LIMITS[subscription.plan_code]
  const meters = {}
  for (const operation of ['campaign', 'render']) {
    meters[operation] = {
      used: usage[operation],
      limit: limits[operation],
      remaining: Math.max(0, limits[operation] - usage[operation]),
      percent: Math.min(100, Math.round(100 * usage[operation] / limits[operation])),
    }
  }
  return {
    plan: subscription.plan_code,
    status: active ? subscription.status : 'EXPIRED_OR_INACTIVE',
    active,
    remainingDays: active ? Math.ceil((Math.min(end, periodEnd) - nowMs) / 86_400_000) : 0,
    validUntil: subscription.valid_until,
    periodEnd: subscription.period_end,
    meters,
  }
}


// Read-only owner guidance. Nothing here renews a plan or changes entitlements.
export function subscriptionNotice(summary) {
  if (!summary || !summary.meters || typeof summary.active !== 'boolean') {
    throw new Error('Verified subscription summary required')
  }
  if (!summary.active) {
    return { level: 'alert', code: 'ACCESS_EXPIRED',
      text: 'Access has expired or is inactive. New AI jobs are blocked; existing drafts remain accessible. Contact the SaaS administrator for a reviewed entitlement change.' }
  }
  if (summary.remainingDays <= 2) {
    return { level: 'warning', code: 'EXPIRING_SOON',
      text: 'Your current access period ends soon. No automatic renewal or paid checkout is enabled.' }
  }
  const exhausted = Object.entries(summary.meters).filter(([, meter]) => meter.remaining === 0)
  if (exhausted.length) {
    return { level: 'warning', code: 'PERIOD_LIMIT_REACHED',
      text: 'A campaign or render allowance is exhausted. New jobs of that type remain blocked until a server-authorized period or entitlement change.' }
  }
  return null
}
