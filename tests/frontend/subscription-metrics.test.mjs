import test from 'node:test'
import assert from 'node:assert/strict'
import { createRetailClient } from '../../frontend/src/lib/supabase.js'
import { PLAN_LIMITS, presentSubscription } from '../../frontend/src/features/subscription/plan-display.mjs'

const SHOP = 'a1000000-0000-4000-8000-000000000001'
const FOREIGN = 'b2000000-0000-4000-8000-000000000001'
const NOW = Date.parse('2026-10-24T12:00:00Z')
function storageForSession() {
  const data = new Map([['retailgrowthai-auth-v1', JSON.stringify({
    access_token: 'user-JWT', refresh_token: 'refresh', expires_at: 2000000000,
  })]])
  return { getItem: key => data.get(key) || null,
    setItem: (key, value) => data.set(key, value), removeItem: key => data.delete(key) }
}
function reply(status, header) {
  return { ok: status >= 200 && status < 300, status,
    headers: { get: key => key.toLowerCase() === 'content-range' ? header : null } }
}

test('client metrics are exact tenant-filtered HEAD reads using user JWT and no personal content', async () => {
  const requests = []
  const client = createRetailClient({
    url: 'https://tenant.supabase.test', key: 'sb_publishable_test',
    storage: storageForSession(), clock: () => NOW,
    fetchImpl: async (url, options) => {
      requests.push({ url: new URL(url), options })
      return reply(200, '0-6/7')
    },
  })
  assert.deepEqual(await client.getShopMetrics(SHOP), {
    campaigns: 7, drafts: 7, reelsReady: 7, rendersProcessing: 7,
  })
  assert.equal(requests.length, 4)
  for (const { url, options } of requests) {
    assert.equal(options.method, 'HEAD')
    assert.equal(options.headers.Authorization, 'Bearer user-JWT')
    assert.equal(options.headers.Prefer, 'count=exact')
    assert.equal(options.headers.apikey, 'sb_publishable_test')
    assert.equal(options.body, undefined)
    assert.equal(url.searchParams.get('shop_id'), 'eq.' + SHOP)
    assert.equal(url.origin, 'https://tenant.supabase.test')
    assert.ok(['campaigns', 'render_jobs'].some(x => url.pathname.endsWith('/' + x)))
  }
  assert.equal(requests[3].url.searchParams.get('status'), 'in.(QUEUED,RUNNING)')
  assert.deepEqual(await client.getShopUsage(SHOP, '2026-10-23T00:00:00Z'), {
    campaign: 7, render: 7,
  })
  assert.equal(requests.length, 6)
  assert.equal(requests[4].url.searchParams.get('period_start'), 'eq.2026-10-23T00:00:00Z')
  assert.equal(requests[4].url.searchParams.get('operation'), 'eq.campaign')
  assert.equal(requests[5].url.searchParams.get('operation'), 'eq.render')
  assert.equal(requests[4].url.searchParams.get('select'), 'job_id')
})

test('missing/opaque count or RLS denial cannot be substituted by zero', async () => {
  for (const [status, range] of [[200, '*/*'], [200, null], [403, null], [200, '*/unknown']]) {
    const client = createRetailClient({
      url: 'https://tenant.supabase.test', key: 'pub',
      storage: storageForSession(), clock: () => NOW,
      fetchImpl: async () => reply(status, range),
    })
    await assert.rejects(client.getShopMetrics(SHOP), /metrics|count/)
  }
  const zero = createRetailClient({
    url: 'https://tenant.supabase.test', key: 'pub',
    storage: storageForSession(), clock: () => NOW,
    fetchImpl: async () => reply(200, '*/0'),
  })
  assert.equal((await zero.getShopMetrics(SHOP)).campaigns, 0)
  await assert.rejects(zero.getShopMetrics('not-uuid'), /Invalid business/)
  await assert.rejects(zero.getShopUsage(FOREIGN, 'not-a-date'), /scope/)
})

test('trial status, limits and overspent caps are presentation only', () => {
  assert.deepEqual(PLAN_LIMITS.TRIAL, { campaign: 2, render: 2 })
  const record = { plan_code: 'TRIAL', status: 'TRIAL', valid_from: '2026-10-23T00:00:00Z',
    valid_until: '2026-10-30T00:00:00Z', period_start: '2026-10-23T00:00:00Z',
    period_end: '2026-10-30T00:00:00Z' }
  const current = presentSubscription(record, { campaign: 1, render: 2 }, NOW)
  assert.equal(current.active, true)
  assert.equal(current.meters.campaign.remaining, 1)
  assert.equal(current.meters.render.remaining, 0)
  assert.equal(current.remainingDays, 6)
  assert.equal(presentSubscription(record, { campaign: 3, render: 2 }, NOW)
    .meters.campaign.percent, 100)
  const expired = presentSubscription(record, { campaign: 1, render: 0 },
    Date.parse('2026-11-01T00:00:00Z'))
  assert.equal(expired.active, false)
  assert.equal(expired.remainingDays, 0)
  assert.throws(() => presentSubscription({ ...record, plan_code: 'UNAPPROVED' },
    { campaign: 0, render: 0 }, NOW))
  assert.throws(() => presentSubscription(record, { campaign: null, render: 0 }, NOW))
})
