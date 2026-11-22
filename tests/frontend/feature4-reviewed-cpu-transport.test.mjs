import test from 'node:test'
import assert from 'node:assert/strict'
import { createVideoTransport } from '../../frontend/src/features/video/video-transport.mjs'

const SHOP = '11111111-1111-4111-8111-111111111111'
const OTHER = '44444444-4444-4444-8444-444444444444'
const CAMPAIGN = '22222222-2222-4222-8222-222222222222'
const PLAN = '99999999-9999-4999-8999-999999999999'
const JOB = '33333333-3333-4333-8333-333333333333'
const LEASE = '55555555-5555-4555-8555-555555555555'
const HASH = 'a'.repeat(64)
const SOURCE = 'https://retailgrowth-dev-functions.azurewebsites.net'
const SUPABASE = 'https://example.supabase.co'
const routes = Object.freeze({
  create: campaign => '/campaigns/' + campaign + '/feature4-renders',
  status: job => '/feature4-render-jobs/' + job,
  download: job => '/feature4-render-jobs/' + job + '/download',
})
const receipt = { shop_id: SHOP, job_id: JOB, status: 'QUEUED' }

function mockResponse(body, status = 202) {
  return { ok: status >= 200 && status < 300, status,
    json: async () => body }
}

function transport(fetchImpl) {
  return createVideoTransport({
    enabled: true, routes, baseUrl: SOURCE, supabaseOrigin: SUPABASE,
    tokenProvider: async () => 'user-owned-JWT-not-service-role',
    fetchImpl,
  })
}

test('reviewed CPU submission sends only persisted plan ID and review SHA, not browser storyboard', async () => {
  const observed = []
  const client = transport(async (url, init) => {
    observed.push({ url, init })
    return mockResponse(receipt)
  })
  const response = await client.createReviewedCpu({
    shopId: SHOP, campaignId: CAMPAIGN, planId: PLAN, reviewHash: HASH,
  })
  assert.equal(observed.length, 1)
  assert.deepEqual(response, { ...receipt, error_code: null })
  assert.equal(observed[0].url, SOURCE + '/api/campaigns/' + CAMPAIGN + '/feature4-renders')
  assert.equal(observed[0].init.method, 'POST')
  assert.equal(observed[0].init.cache, 'no-store')
  assert.equal(observed[0].init.headers.Authorization, 'Bearer user-owned-JWT-not-service-role')
  assert.deepEqual(JSON.parse(observed[0].init.body), {
    plan_id: PLAN, expected_review_hash: HASH,
  })
  assert.equal(observed[0].init.signal, undefined)
})

test('unknown plan, mixed-case IDs, invalid SHA cannot reach server', async () => {
  let sends = 0
  const client = transport(async () => { sends++; return mockResponse(receipt) })
  for (const wrong of [
    { planId: '../foreign' },
    { shopId: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'.toUpperCase() },
    { campaignId: 'bad' },
    { reviewHash: 'not-a-reviewed-digest' },
    { reviewHash: 'f'.repeat(65) },
  ]) {
    await assert.rejects(() => client.createReviewedCpu({
      shopId: SHOP, campaignId: CAMPAIGN, planId: PLAN, reviewHash: HASH, ...wrong,
    }))
  }
  assert.equal(sends, 0)
})

test('foreign/malformed backend receipt and uncertain POST ACK are never accepted/retried', async () => {
  let sends = 0
  const first = transport(async () => {
    sends++; return mockResponse({ ...receipt, shop_id: OTHER })
  })
  await assert.rejects(() => first.createReviewedCpu({
    shopId: SHOP, campaignId: CAMPAIGN, planId: PLAN, reviewHash: HASH,
  }), /tenant/)
  const lost = transport(async () => {
    sends++; throw new TypeError('lost acknowledgement after job commit')
  })
  await assert.rejects(() => lost.createReviewedCpu({
    shopId: SHOP, campaignId: CAMPAIGN, planId: PLAN, reviewHash: HASH,
  }), /lost acknowledgement/)
  assert.equal(sends, 2)
})

test('a CPU render is only downloadable with a current private shop+job signed URL', async () => {
  const signed = SUPABASE + '/storage/v1/object/sign/retailgrowth-media/' +
    SHOP + '/renders/' + JOB + '/' + LEASE + '.mp4?token=short'
  const client = transport(async (url, init) => {
    assert.equal(init.method, 'GET')
    if (url.endsWith('/download')) return mockResponse({
      shop_id: SHOP, job_id: JOB, url: signed,
    }, 200)
    return mockResponse({ ...receipt, status: 'SUCCEEDED' }, 200)
  })
  assert.equal((await client.status({ jobId: JOB, shopId: SHOP })).status, 'SUCCEEDED')
  assert.equal(await client.download({ jobId: JOB, shopId: SHOP }), signed)
})

test('review UI is opt-in only; no client-owned approval or automatic POST', async () => {
  const fs = await import('node:fs/promises')
  const ui = await fs.readFile(new URL('../../frontend/src/features/video/CreativePlanReview.jsx', import.meta.url), 'utf8')
  assert.match(ui, /VITE_FEATURE4_CPU_RENDER_ENABLED/)
  assert.match(ui, /plan\.state === 'APPROVED'/)
  assert.match(ui, /createReviewedCpu/)
  assert.match(ui, /cpuApi\.status/)
  assert.match(ui, /cpuApi\.download/)
  assert.match(ui, /setCpuJob\(null\)/)
  assert.doesNotMatch(ui, /approved:\s*true\s*,\s*shop_id/)
})
