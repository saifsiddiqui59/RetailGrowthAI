import test from 'node:test'
import assert from 'node:assert/strict'
import { createTraceStore } from '../../frontend/src/features/testing/trace-store.mjs'

const SHOP = '11111111-1111-4111-8111-111111111111'
const OTHER = '55555555-5555-4555-8555-555555555555'
const JOB = '22222222-2222-4222-8222-222222222222'
const JOB2 = '44444444-4444-4444-8444-444444444444'
const SPAN = '33333333-3333-4333-8333-333333333333'
const evidence = (job = JOB) => ({
  id: job === JOB ? SPAN : JOB2, shop_id: SHOP, job_id: job, feature: 'F2',
  operation: 'planning.complete', status: 'SUCCEEDED',
  attempt: 1, elapsed_ms: 450, metadata: { generated_days: 7, planner_mode: 'dev_mock' },
  recorded_at: '2026-11-18T00:00:00Z',
})
const payload = (job = JOB) => ({
  source: 'trusted_backend_persisted', shop_id: SHOP,
  job_id: job, events: [evidence(job)],
})
const response = (status, json) => ({
  ok: status >= 200 && status < 300,
  status,
  json: async () => json,
})
const client = (fetchImpl, tokenProvider = async () => 'signed-retailer-jwt') =>
  createTraceStore({
    supabaseUrl: 'https://tenant.supabase.co',
    publishableKey: 'sb_publishable_fake_test_only',
    tokenProvider,
    fetchImpl,
  })

test('current trusted span reader uses signed shop JWT, never service key or private table', async () => {
  let seen
  const store = client(async (url, init) => {
    seen = { url, init }
    return response(200, payload())
  })
  const rows = await store.listWorkerSpans(SHOP, [JOB])
  assert.equal(rows.length, 1)
  assert.equal(rows[0].status, 'SUCCEEDED')
  assert.equal(seen.url, 'https://tenant.supabase.co/rest/v1/rpc/retail_feature_worker_spans')
  assert.equal(seen.init.method, 'POST')
  assert.equal(seen.init.redirect, 'error')
  assert.equal(seen.init.cache, 'no-store')
  assert.equal(seen.init.headers.Authorization, 'Bearer signed-retailer-jwt')
  assert.equal(seen.init.headers.apikey, 'sb_publishable_fake_test_only')
  assert.deepEqual(JSON.parse(seen.init.body), {
    p_shop_id: SHOP, p_job_id: JOB, p_limit: 10,
  })
  assert.equal(JSON.stringify(seen.init).includes('service_role'), false)
})

test('two current known jobs use separate bounded signed RPC reads', async () => {
  const calls = []
  const store = client(async (_url, init) => {
    const body = JSON.parse(init.body)
    calls.push(body)
    return response(200, payload(body.p_job_id))
  })
  const rows = await store.listWorkerSpans(SHOP, [JOB, JOB2])
  assert.equal(rows.length, 2)
  assert.deepEqual(calls.map(x => x.p_job_id), [JOB, JOB2])
  assert(calls.every(x => x.p_limit === 10 && x.p_shop_id === SHOP))
})

test('foreign tenant, foreign job, invalid feature/status/attempt/duration and untrusted source fail closed', async () => {
  const good = payload()
  const cases = [
    { ...good, source: 'browser_observed' },
    { ...good, shop_id: OTHER },
    { ...good, job_id: JOB2 },
    { ...good, events: [{ ...evidence(), shop_id: OTHER }] },
    { ...good, events: [{ ...evidence(), job_id: JOB2 }] },
    { ...good, events: [{ ...evidence(), feature: 'F5' }] },
    { ...good, events: [{ ...evidence(), status: 'QUEUED' }] },
    { ...good, events: [{ ...evidence(), attempt: 0 }] },
    { ...good, events: [{ ...evidence(), attempt: 6 }] },
    { ...good, events: [{ ...evidence(), elapsed_ms: 1800001 }] },
    { ...good, events: Array.from({ length: 11 }, () => evidence()) },
    { ...good, events: 'not an array' },
  ]
  for (const invalid of cases) {
    const store = client(async () => response(200, invalid))
    await assert.rejects(
      () => store.listWorkerSpans(SHOP, [JOB]),
      /inconsistent tenant or source/,
    )
  }
})

test('missing or forbidden backend RPC must never appear to be verified worker output', async () => {
  for (const status of [401, 403, 404, 406, 500]) {
    const store = client(async () => response(status, { error: 'unavailable' }))
    await assert.rejects(() => store.listWorkerSpans(SHOP, [JOB]))
  }
})

test('invalid shop, job list, duplicates and more than five jobs are rejected before network', async () => {
  let calls = 0
  const store = client(async () => { calls++; return response(200, payload()) })
  const invalid = [
    [OTHER.slice(0, -2), [JOB]],
    [SHOP, []],
    [SHOP, 'not an array'],
    [SHOP, [JOB, JOB]],
    [SHOP, ['foreign-job-id']],
    [SHOP, [JOB, JOB2, OTHER, SPAN, '66666666-6666-4666-8666-666666666666', '77777777-7777-4777-8777-777777777777']],
  ]
  for (const [shop, ids] of invalid) {
    await assert.rejects(() => store.listWorkerSpans(shop, ids))
  }
  assert.equal(calls, 0)
})

test('no signed user JWT denies trusted worker read before any Supabase HTTP', async () => {
  let calls = 0
  const store = client(async () => { calls++; return response(200, payload()) }, async () => '')
  await assert.rejects(() => store.listWorkerSpans(SHOP, [JOB]), /Sign in/)
  assert.equal(calls, 0)
})

test('trace reader must refuse untrusted HTTP or credential-bearing Supabase origin', () => {
  for (const supabaseUrl of [
    'http://tenant.supabase.co',
    'https://user:password@tenant.supabase.co',
    'https://tenant.supabase.co/foreign/path',
    'https://tenant.supabase.co.attacker.test',
    'https://attacker.test',
    'https://tenant.supabase.co:8443',
    'https://tenant.supabase.co@attacker.test',
    'https://tenant.supabase.co.evil.supabase.co',
  ]) {
    assert.throws(() => createTraceStore({
      supabaseUrl, publishableKey: 'test', tokenProvider: async () => 'signed',
      fetchImpl: async () => response(200, payload()),
    }), /trusted HTTPS origin/)
  }
})
