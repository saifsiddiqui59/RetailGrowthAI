import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { readFeature4CpuJobForPlan } from '../../frontend/src/features/video/feature4-cpu-job-history.mjs'

const SHOP = '11111111-1111-4111-8111-111111111111'
const PLAN = '22222222-2222-4222-8222-222222222222'
const JOB = '33333333-3333-4333-8333-333333333333'
const FOREIGN = '44444444-4444-4444-8444-444444444444'
const SUPABASE = 'https://dev-test.supabase.co'
const TOKEN = 'jwt-for-signed-retailer'
const KEY = 'sb_publishable_dev_test'
const row = { id: JOB, shop_id: SHOP, plan_id: PLAN, status: 'SUCCEEDED' }
const reply = (data, status = 200) => ({
  ok: status >= 200 && status < 300,
  json: async () => data,
})
function lookup(fetchImpl, overrides = {}) {
  return readFeature4CpuJobForPlan({
    shopId: SHOP, planId: PLAN, supabaseUrl: SUPABASE,
    publishableKey: KEY, tokenProvider: async () => TOKEN,
    fetchImpl, ...overrides,
  })
}

test('CPU job resume reads only same-shop and exact approved plan under JWT/RLS; never POST', async () => {
  let requests = 0
  const found = await lookup(async (url, options) => {
    requests++
    const u = new URL(url)
    assert.equal(u.origin, SUPABASE)
    assert.equal(u.pathname, '/rest/v1/feature4_cpu_render_jobs')
    assert.equal(u.searchParams.get('select'), 'id,shop_id,plan_id,status')
    assert.equal(u.searchParams.get('shop_id'), 'eq.' + SHOP)
    assert.equal(u.searchParams.get('plan_id'), 'eq.' + PLAN)
    assert.equal(u.searchParams.get('limit'), '2')
    assert.equal(u.searchParams.has('token'), false)
    assert.equal(options.method, 'GET')
    assert.equal(options.redirect, 'error')
    assert.equal(options.cache, 'no-store')
    assert.equal(options.headers.Authorization, 'Bearer ' + TOKEN)
    assert.equal(options.headers.apikey, KEY)
    assert.equal(options.body, undefined)
    return reply([row])
  })
  assert.equal(requests, 1)
  assert.deepEqual(found, row)
  assert.equal(Object.isFrozen(found), true)
})

test('a genuinely absent private job returns null without submitting another render', async () => {
  let requests = 0
  assert.equal(await lookup(async () => { requests++; return reply([]) }), null)
  assert.equal(requests, 1)
})

test('foreign, wrong plan, duplicate, invalid status or malformed responses fail closed', async () => {
  for (const result of [
    [{ ...row, shop_id: FOREIGN }],
    [{ ...row, plan_id: FOREIGN }],
    [{ ...row, id: '../unsafe' }],
    [{ ...row, status: 'PENDING' }],
    [row, row],
    { id: JOB },
    null,
  ]) {
    await assert.rejects(() => lookup(async () => reply(result)),
      /private render history|Private render history|Ambiguous private render/)
  }
})

test('no JWT, invalid shop, unsafe origin and 503 denial block reads without fallback', async () => {
  let requests = 0
  const fetchImpl = async () => { requests++; return reply([row]) }
  for (const overrides of [
    { shopId: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa'.toUpperCase() },
    { planId: 'not-a-plan' },
    { supabaseUrl: 'http://dev-test.supabase.co' },
    { supabaseUrl: 'https://dev-test.supabase.co/elsewhere' },
    { tokenProvider: async () => '' },
    { tokenProvider: async () => 'bad\nheader' },
    { publishableKey: 'sb_secret_x' + '\n' },
  ]) {
    await assert.rejects(() => lookup(fetchImpl, overrides))
  }
  assert.equal(requests, 0)
  await assert.rejects(() => lookup(async () => reply({ error:'unavailable' },503)),
    /Private render history could not be verified/)
})

test('Creative Studio recovers history with GET and forces a fresh private signed URL', async () => {
  const ui = await readFile(new URL('../../frontend/src/features/video/CreativePlanReview.jsx', import.meta.url), 'utf8')
  const parent = await readFile(new URL('../../frontend/src/features/dashboard/CreativeLaunchpad.jsx', import.meta.url), 'utf8')
  assert.match(ui, /readFeature4CpuJobForPlan/)
  assert.match(ui, /history\.isSuccess/)
  assert.match(ui, /history\.refetch\(\)/)
  assert.match(ui, /const latest = await history\.refetch\(\)/)
  assert.match(ui, /if \(!latest\.isSuccess \|\| latest\.data\)/)
  assert.match(ui, /Resume existing render \(no new job\)/)
  assert.match(ui, /cpuApi\.status\(\{ jobId: existing\.id, shopId \}\)/)
  assert.match(ui, /cpuApi\.download\(\{ jobId: existing\.id, shopId \}\)/)
  assert.match(ui, /submissionUncertain/)
  assert.match(parent, /key=\{.*user\?\.id.*shopId/)
})
