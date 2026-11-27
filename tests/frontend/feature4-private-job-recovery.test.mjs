import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { findFeature4CpuRenderJob } from '../../frontend/src/features/video/feature4-cpu-job-recovery.mjs'

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
function fixture(handler, config = {}) {
  const calls = []
  const lookup = (override = {}) => findFeature4CpuRenderJob({
    shopId: SHOP, planId: PLAN, reviewHash: HASH,
    supabaseOrigin: 'https://retailgrowth-dev.example.supabase.co',
    publishableKey: 'sb_publishable_only_test',
    tokenProvider: async () => 'signed-tenant-jwt',
    fetchImpl: async (url, init) => {
      calls.push({ url, init })
      return handler(url, init)
    },
    ...config, ...override,
  })
  return { lookup, calls }
}

test('existing once-per-plan job recovers only via signed RLS GET, no POST or quota', async () => {
  const { lookup, calls } = fixture(() => response([row]))
  const recovered = await lookup()
  assert.deepEqual(recovered, {
    job_id: JOB, shop_id: SHOP, campaign_id: CAMPAIGN,
    plan_id: PLAN, status: 'QUEUED',
  })
  assert.equal(calls.length, 1)
  assert.equal(calls[0].init.method, 'GET')
  assert.equal(calls[0].init.redirect, 'error')
  assert.equal(calls[0].init.cache, 'no-store')
  assert.equal(calls[0].init.credentials, 'omit')
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

test('no job returns null; invalid resource/hash or URL never sends a request', async () => {
  const { lookup, calls } = fixture(() => response([]))
  assert.equal(await lookup(), null)
  const before = calls.length
  for (const wrong of [
    { shopId: 'invalid-shop' },
    { planId: 'not-a-uuid' },
    { reviewHash: 'fake-hash' },
    { supabaseOrigin: 'http://retailgrowth-dev.example.supabase.co' },
    { supabaseOrigin: 'https://malicious.example/path' },
    { publishableKey: 'not-valid' },
    { tokenProvider: async () => 'invalid token with space' },
  ]) {
    await assert.rejects(() => lookup(wrong))
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
    const { lookup, calls } = fixture(() => response(payload))
    await assert.rejects(() => lookup(), /tenant, revision or status verification/)
    assert.equal(calls.length, 1)
  }
})

test('unavailable RLS read is not mistaken for no job and does not replay POST', async () => {
  const { lookup, calls } = fixture(() => response({ code: 'DEV_OFFLINE' }, 503))
  await assert.rejects(() => lookup(), /history unavailable/)
  assert.equal(calls.length, 1)
  assert.equal(calls[0].init.method, 'GET')
})

test('UI recovery requires explicit click, verified status and renewed signed link', async () => {
  const ui = await readFile(new URL(
    '../../frontend/src/features/video/CreativePlanReview.jsx', import.meta.url), 'utf8')
  assert.match(ui, /async function recoverCpuRender\(\)/)
  assert.match(ui, /onClick=\{recoverCpuRender\}/)
  assert.match(ui, /await findFeature4CpuRenderJob\(\{/)
  assert.match(ui, /cpuApi\.status\(/)
  assert.match(ui, /cpuApi\.download\(/)
  assert.match(ui, /Check existing render \(read only\)/)
  const poll = ui.slice(ui.indexOf('async function refresh()'),
    ui.indexOf('async function downloadCpu()'))
  assert.ok(poll.indexOf('signed = await cpuApi.download(') >= 0)
  assert.ok(poll.indexOf('signed = await cpuApi.download(') <
    poll.indexOf('setCpuJob({ ...verified, planId: currentPlan })'),
    'signed preview renewal must precede terminal job state effect cleanup')
  assert.doesNotMatch(ui.slice(ui.indexOf('async function recoverCpuRender()'),
    ui.indexOf('async function submitCpuRender()')), /createReviewedCpu|feature4_submit_cpu_render/)
})


test('new render requires a fresh signed revision lookup and a synchronous once-per-plan guard', async () => {
  const ui = await readFile(new URL(
    '../../frontend/src/features/video/CreativePlanReview.jsx', import.meta.url), 'utf8')
  const submit = ui.slice(ui.indexOf('async function submitCpuRender()'),
    ui.indexOf('  useEffect(() => {', ui.indexOf('async function submitCpuRender()')))
  const lookup = submit.indexOf('await findFeature4CpuRenderJob(')
  const post = submit.indexOf('await cpuApi.createReviewedCpu(')
  assert.ok(lookup >= 0 && post > lookup)
  assert.ok(submit.indexOf('cpuSubmitBusy.current = true') < lookup)
  assert.ok(submit.indexOf('attemptedPlans.current.add(plan.id)') < post)
  assert.match(submit, /if \(existing\) \{[\s\S]*?return\s*\}/)
  assert.match(submit, /existing.campaign_id !== plan.campaign_id/)
  assert.match(submit, /attemptedPlans.current.has\(plan.id\)/)
  assert.doesNotMatch(submit, /attemptedPlans.current.delete/)
  assert.match(ui, /disabled=\{working \|\| lockedPlans.includes\(plan.id\)/)
})

test('private review state remounts on authenticated actor, business or role change', async () => {
  const launchpad = await readFile(new URL(
    '../../frontend/src/features/dashboard/CreativeLaunchpad.jsx', import.meta.url), 'utf8')
  assert.match(launchpad, /<CreativePlanReview key=\{JSON.stringify\(\[user.id, shopId, shops.find\(item => item.id === shopId\)\?\.membership\?\.role \|\| null\]\)\}/)
})
