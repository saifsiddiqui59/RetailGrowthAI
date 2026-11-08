import test from 'node:test'
import assert from 'node:assert/strict'
import {
  canonicalVideoId, trustedVideoPath, privateVideoUrl, privateMediaPreviewUrl,
  parseVideoJob, createVideoTransport,
} from '../../frontend/src/features/video/video-transport.mjs'

const SHOP = '11111111-1111-4111-8111-111111111111'
const OTHER = '44444444-4444-4444-8444-444444444444'
const CAMPAIGN = '22222222-2222-4222-8222-222222222222'
const JOB = '33333333-3333-4333-8333-333333333333'
const LEASE = '55555555-5555-4555-8555-555555555555'
const SU = 'https://example.supabase.co'
const ORIGIN = 'https://retailgrowth-dev-functions.azurewebsites.net'
const routes = {
  create: campaign => '/campaigns/' + campaign + '/creative-renders',
  status: job => '/creative-render-jobs/' + job,
  download: job => '/creative-render-jobs/' + job + '/download',
}
const signed = SU + '/storage/v1/object/sign/retailgrowth-media/' +
  SHOP + '/renders/' + JOB + '/' + LEASE + '.mp4?token=private-example'
const draft = { version: 'rg_video_v2', shop_id: SHOP, duration_seconds: 30, scenes: [] }
const accepted = { shop_id: SHOP, job_id: JOB, status: 'QUEUED' }
function response(data, status = 200) {
  return { ok: status >= 200 && status < 300, status, json: async () => data }
}
function fixture(fn, options = {}) {
  return createVideoTransport({ enabled: true, baseUrl: ORIGIN,
    tokenProvider: () => 'example-tenant-jwt',
    fetchImpl: fn, routes, supabaseOrigin: SU, ...options })
}

test('integration client default off and strict config', () => {
  assert.equal(createVideoTransport({}), null)
  assert.throws(() => createVideoTransport({ enabled: true }), /routes and auth/)
  assert.throws(() => fixture(async () => response(accepted), { baseUrl: 'http://untrusted.invalid' }), /HTTPS/)
  assert.throws(() => fixture(async () => response(accepted), { baseUrl: ORIGIN + '/api' }), /HTTPS/)
  assert.throws(() => fixture(async () => response(accepted), { timeoutMs: 60000 }), /timeout/)
})

test('POST sends one authenticated job intent with no service role, no retries', async () => {
  const seen = []
  const api = fixture(async (url, opts) => {
    seen.push({ url, opts })
    return response(accepted, 202)
  })
  const job = await api.create({ shopId: SHOP, campaignId: CAMPAIGN,
    draft, approvalId: 'approved-feature2-copy' })
  assert.deepEqual(job, { ...accepted, error_code: null })
  assert.equal(seen.length, 1)
  assert.equal(seen[0].url, ORIGIN + '/api/campaigns/' + CAMPAIGN + '/creative-renders')
  assert.equal(seen[0].opts.headers.Authorization, 'Bearer example-tenant-jwt')
  assert.equal(seen[0].opts.cache, 'no-store')
  assert.equal(seen[0].opts.method, 'POST')
  assert.equal(seen[0].opts.signal, undefined)
  assert.deepEqual(JSON.parse(seen[0].opts.body),
    { shop_id: SHOP, campaign_id: CAMPAIGN, approval_id: 'approved-feature2-copy', draft })
})

test('POST never retries a lost acknowledgement or transient 503', async () => {
  let calls = 0
  const api = fixture(async () => { calls++; throw new TypeError('network dropped after commit') })
  await assert.rejects(() => api.create({ shopId: SHOP, campaignId: CAMPAIGN,
    draft, approvalId: 'version1' }), /network dropped/)
  assert.equal(calls, 1)
  const unavailable = fixture(async () => { calls++; return response({ error: 'SERVICE_UNAVAILABLE' }, 503) })
  await assert.rejects(() => unavailable.create({ shopId: SHOP, campaignId: CAMPAIGN,
    draft, approvalId: 'version1' }), /Check job status before resubmitting/)
  assert.equal(calls, 2)
})

test('reject unauthorized, misbound or fabricated job receipt', async () => {
  for (const bad of [
    { ...accepted, shop_id: OTHER }, { ...accepted, job_id: 'not-a-uuid' },
    { ...accepted, status: 'FINISHED' }, { ...accepted, status: 'SUCCEEDED', shop_id: undefined },
  ]) {
    const api = fixture(async () => response(bad, 202))
    await assert.rejects(() => api.create({
      shopId: SHOP, campaignId: CAMPAIGN, draft, approvalId: 'approved'
    }), /tenant\/status verification|canonical resource ID/)
  }
  await assert.rejects(() => fixture(async () => response(accepted)).create({
    shopId: OTHER, campaignId: CAMPAIGN, draft, approvalId: 'approved',
  }), /reviewed video draft/)
})

test('GET status binds both job and shop; requests freshly scoped JWT', async () => {
  let count = 0
  const api = fixture(async (url, opts) => {
    count++
    assert.equal(opts.method, 'GET')
    assert.ok(opts.signal)
    assert.equal(url, ORIGIN + '/api/creative-render-jobs/' + JOB)
    return response({ ...accepted, status: 'RUNNING' })
  })
  const item = await api.status({ jobId: JOB, shopId: SHOP })
  assert.equal(item.status, 'RUNNING')
  assert.equal(count, 1)
  const wrong = fixture(async () => response({ ...accepted, job_id: OTHER }))
  await assert.rejects(() => wrong.status({ jobId: JOB, shopId: SHOP }), /requested job/)
})

test('download requires matching shop+job and signed private tenant path', async () => {
  const api = fixture(async () => response({ ...accepted, url: signed }))
  assert.equal(await api.download({ shopId: SHOP, jobId: JOB }), signed)
  const invalid = fixture(async () => response({ ...accepted, shop_id: OTHER, url: signed }))
  await assert.rejects(() => invalid.download({ shopId: SHOP, jobId: JOB }), /receipt/)
  const wrongUrl = fixture(async () => response({
    ...accepted, url: signed.replace(SHOP, OTHER)
  }))
  await assert.rejects(() => wrongUrl.download({ shopId: SHOP, jobId: JOB }), /does not belong/)
})

test('malicious signed links cannot cross tenant, job, origin or protocol', () => {
  assert.equal(privateVideoUrl(signed, SU, SHOP, JOB), signed)
  for (const value of [
    signed.replace(SHOP, OTHER),
    signed.replace(JOB, OTHER),
    signed.replace('example.supabase.co', 'attacker.invalid'),
    signed.replace('https:', 'http:'),
    signed.replace('token=', 'not-token='),
    signed.replace('/sign/', '/public/'),
    signed + '#token-secret',
    signed.replace('/renders/', '/renders/%2e%2e/'),
  ]) {
    assert.throws(() => privateVideoUrl(value, SU, SHOP, JOB), /Signed|Unsigned|private|belong|Malformed/)
  }
})

test('unreviewed route/path and session IDs fail closed', async () => {
  assert.equal(canonicalVideoId(SHOP), SHOP)
  for (const id of ['aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'.toUpperCase(), 'not-a-uuid', '']) {
    assert.throws(() => canonicalVideoId(id), /canonical/)
  }
  for (const path of ['//evil.invalid/render', '/api/video', '/../../admin', '/creative-renders?token=a']) {
    assert.throws(() => trustedVideoPath(path), /Invalid/)
  }
  const api = fixture(async () => response(accepted), { routes: {
    ...routes, create: () => '//attacker.invalid/v2',
  } })
  await assert.rejects(() => api.create({
    shopId: SHOP, campaignId: CAMPAIGN, draft, approvalId: 'approved',
  }), /Invalid versioned video API path/)
})

test('parse video job never accepts cross-shop result even if server says succeeded', () => {
  assert.deepEqual(parseVideoJob({ ...accepted, status: 'SUCCEEDED' }, SHOP),
    { ...accepted, status: 'SUCCEEDED', error_code: null })
  assert.throws(() => parseVideoJob({ ...accepted, shop_id: OTHER }, SHOP), /tenant/)
  assert.throws(() => parseVideoJob({ ...accepted, job_id: OTHER }, SHOP, JOB), /requested job/)
})

test('Feature4 source previews require a matching signed tenant-private Storage asset', () => {
  const url = SU + '/storage/v1/object/sign/retailgrowth-media/' +
    SHOP + '/products/original-kurti.png?token=short-lived'
  assert.equal(privateMediaPreviewUrl(url, SU, SHOP), url)
  for (const bad of [
    url.replace(SHOP, OTHER),
    url.replace('https://', 'http://'),
    url.replace('/sign/', '/public/'),
    url.replace('example.supabase.co', 'untrusted.invalid'),
    url.replace('token=', 'not-token='),
    url.replace('/products/', '/products/%2e%2e/'),
    url + '#leaked',
    'data:image/svg+xml;base64,PHN2Zz4=',
  ]) {
    assert.throws(() => privateMediaPreviewUrl(bad, SU, SHOP), /preview|signed|private|Storage|shop|unsafe|URL/)
  }
})
