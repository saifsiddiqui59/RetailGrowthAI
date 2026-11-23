import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { createRetailClient } from '../../frontend/src/lib/supabase.js'

const SHOP = '11111111-1111-4111-8111-111111111111'
const FOREIGN = '22222222-2222-4222-8222-222222222222'
const PLAN = '33333333-3333-4333-8333-333333333333'
const CAMPAIGN = '44444444-4444-4444-8444-444444444444'
const JOB = '55555555-5555-4555-8555-555555555555'
const HASH = 'a'.repeat(64)
const row = {
  id: JOB, shop_id: SHOP, campaign_id: CAMPAIGN, plan_id: PLAN,
  approved_review_sha256: HASH, status: 'QUEUED',
}

const response = (payload, status = 200) => new Response(JSON.stringify(payload), {
  status, headers: { 'content-type': 'application/json' },
})
const storage = () => {
  const data = new Map()
  return {
    getItem: key => data.get(key) || null,
    setItem: (key, value) => data.set(key, value),
    removeItem: key => data.delete(key),
  }
}
function client(handler) {
  const calls = []
  const api = createRetailClient({
    url: 'https://retailgrowth-dev.example.supabase.co',
    key: 'sb_publishable_only_test',
    storage: storage(),
    fetchImpl: async (url, init) => {
      if (url.includes('/auth/v1/token')) return response({
        access_token: 'signed-tenant-jwt', refresh_token: 'tenant-refresh',
        expires_in: 3600,
      })
      calls.push({ url, init })
      return handler(url, init)
    },
  })
  return { api, calls }
}

test('existing once-per-plan job recovers only via signed RLS GET, no POST or quota', async () => {
  const { api, calls } = client(() => response([row]))
  await api.signIn('owner@example.invalid', 'test-password')
  const recovered = await api.findFeature4CpuRenderJob(SHOP, PLAN, HASH)
  assert.deepEqual(recovered, {
    job_id: JOB, shop_id: SHOP, campaign_id: CAMPAIGN,
    plan_id: PLAN, status: 'QUEUED',
  })
  assert.equal(calls.length, 1)
  assert.equal(calls[0].init.method, 'GET')
  assert.equal(calls[0].init.headers.Authorization, 'Bearer signed-tenant-jwt')
  assert.equal(calls[0].init.headers.apikey, 'sb_publishable_only_test')
  const url = new URL(calls[0].url)
  assert.equal(url.pathname, '/rest/v1/feature4_cpu_render_jobs')
  assert.equal(url.searchParams.get('shop_id'), 'eq.' + SHOP)
  assert.equal(url.searchParams.get('plan_id'), 'eq.' + PLAN)
  assert.equal(url.searchParams.get('limit'), '2')
  assert.equal(url.searchParams.get('select'),
    'id,shop_id,campaign_id,plan_id,approved_review_sha256,status')
  assert.doesNotMatch(JSON.stringify(calls), /service_role|sb_secret_|submit_cpu_render/)
})

test('no job returns null; invalid business/hash does not contact backend', async () => {
  const { api, calls } = client(() => response([]))
  await api.signIn('owner@example.invalid', 'test-password')
  assert.equal(await api.findFeature4CpuRenderJob(SHOP, PLAN, HASH), null)
  const before = calls.length
  for (const args of [
    [FOREIGN.toUpperCase(), PLAN, HASH],
    [SHOP, 'not-a-uuid', HASH],
    [SHOP, PLAN, 'fake-hash'],
  ]) {
    await assert.rejects(() => api.findFeature4CpuRenderJob(...args),
      /verified business/)
  }
  assert.equal(calls.length, before)
})

test('foreign, stale, forged and ambiguous job rows are rejected fail-closed', async () => {
  const variants = [
    [{ ...row, shop_id: FOREIGN }],
    [{ ...row, plan_id: FOREIGN }],
    [{ ...row, approved_review_sha256: 'b'.repeat(64) }],
    [{ ...row, campaign_id: 'bad' }],
    [{ ...row, status: 'APPROVED' }],
    [{ ...row, id: 'invalid-job' }],
    [row, row],
    { status: 'SUCCEEDED' },
  ]
  for (const payload of variants) {
    const { api, calls } = client(() => response(payload))
    await api.signIn('owner@example.invalid', 'test-password')
    await assert.rejects(() => api.findFeature4CpuRenderJob(SHOP, PLAN, HASH),
      /private business\/revision verification/)
    assert.equal(calls.length, 1)
  }
})

test('unavailable RLS read is not mistaken for no job and does not replay POST', async () => {
  const { api, calls } = client(() => response({ code: 'DEV_OFFLINE' }, 503))
  await api.signIn('owner@example.invalid', 'test-password')
  await assert.rejects(() => api.findFeature4CpuRenderJob(SHOP, PLAN, HASH))
  assert.equal(calls.length, 1)
  assert.equal(calls[0].init.method, 'GET')
})

test('UI recovery requires explicit click and renews GET status/private signed link', async () => {
  const ui = await readFile(new URL(
    '../../frontend/src/features/video/CreativePlanReview.jsx', import.meta.url), 'utf8')
  assert.match(ui, /async function recoverCpuRender\(\)/)
  assert.match(ui, /onClick=\{recoverCpuRender\}/)
  assert.match(ui, /client\.findFeature4CpuRenderJob\(/)
  assert.match(ui, /cpuApi\.status\(/)
  assert.match(ui, /cpuApi\.download\(/)
  assert.match(ui, /Check existing render \(read only\)/)
  assert.doesNotMatch(ui.slice(ui.indexOf('async function recoverCpuRender()'),
    ui.indexOf('async function submitCpuRender()')), /createReviewedCpu|feature4_submit_cpu_render/)
})
