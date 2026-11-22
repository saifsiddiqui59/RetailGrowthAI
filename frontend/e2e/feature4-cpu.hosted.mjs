// Opt-in real signed DEV Feature2 -> Feature4 CPU acceptance. Not standard CI.
// Does not create users, bypass onboarding, invent media rights, or start paid AI.
// Existing approved synthetic test shops and a saved F2 campaign/day are required.
import { test, expect } from '@playwright/test'
import { spawnSync } from 'node:child_process'
import { mkdtempSync, rmSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { hostedConfig, pollHosted, signedDownloadUrl } from './hosted-support.mjs'

const cfg = hostedConfig(process.env)
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i
const SHA = /^[0-9a-f]{64}$/
const API = cfg.api + '/api'
const noRetry = { failOnStatusCode: false, timeout: 30000, maxRetries: 0 }
const state = { planId: '', sourceHash: '', reviewHash: '', jobId: '', actorJwt: '' }
const expectedConsent = 'I_APPROVE_SYNTHETIC_FEATURE4_DEV_RENDER_TEST'
const campaignId = String(process.env.RG_F4_E2E_CAMPAIGN_ID || '').trim()
const dayId = String(process.env.RG_F4_E2E_DAY_ID || '').trim()

if (!UUID.test(campaignId) || !UUID.test(dayId)) {
  throw new Error('A real saved, rights-approved DEV campaign/day UUID is required for F4 E2E')
}
if (process.env.RG_F4_E2E_TEST_RENDER_CONSENT !== expectedConsent) {
  throw new Error('Explicit test-only Feature4 render consent is required; no customer billing')
}
if (process.env.RG_F4_E2E_WORKER_VERIFIED !== 'YES') {
  throw new Error('Real isolated DEV CPU worker/queue proof is required before test render')
}

async function json(res) {
  try { return await res.json() }
  catch { throw new Error('Expected JSON; HTTP ' + res.status()) }
}
function auth(token) { return { Authorization: 'Bearer ' + token } }
async function call(request, token, method, route, data) {
  return request.fetch(API + route, {
    method, headers: { ...auth(token),
      ...(data === undefined ? {} : { 'Content-Type': 'application/json' }) },
    ...(data === undefined ? {} : { data }), ...noRetry,
  })
}
async function login(request, account) {
  const response = await request.post(cfg.supabase + '/auth/v1/token?grant_type=password', {
    headers: { apikey: cfg.publishable, 'Content-Type': 'application/json' },
    data: { email: account.email, password: account.password }, ...noRetry,
  })
  expect(response.status(), 'Real Supabase password sign-in').toBe(200)
  const payload = await json(response)
  expect(typeof payload.access_token).toBe('string')
  expect(payload.access_token.split('.')).toHaveLength(3)
  return payload.access_token
}
async function membership(request, jwt, shopId) {
  const result = await request.get(
    cfg.supabase + '/rest/v1/shop_memberships?select=shop_id,role,active&active=eq.true', {
      headers: { ...auth(jwt), apikey: cfg.publishable }, ...noRetry,
    })
  expect(result.status()).toBe(200)
  const rows = await json(result)
  const owned = rows.find(x => x.shop_id === shopId && x.active === true)
  expect(owned, 'Signed test actor has an actual active shop membership').toBeTruthy()
  return rows
}
function denied(res) { expect([403, 404], 'Foreign tenant denied').toContain(res.status()) }
function privateMp4(bytes, seconds) {
  expect(bytes.length).toBeGreaterThan(10000)
  expect(bytes.length).toBeLessThanOrEqual(80 * 1024 * 1024)
  const dir = mkdtempSync(join(tmpdir(), 'rgai-f4-private-'))
  try {
    const file = join(dir, 'render.mp4')
    writeFileSync(file, bytes, { mode: 0o600 })
    const output = spawnSync('ffprobe', [
      '-v', 'error', '-show_entries',
      'format=duration:stream=codec_type,codec_name,width,height',
      '-of', 'json', file,
    ], { encoding: 'utf8', maxBuffer: 1024 * 1024, timeout: 30000 })
    expect(output.error).toBeFalsy()
    expect(output.status, 'Real FFprobe on retrieved private object').toBe(0)
    const probe = JSON.parse(output.stdout)
    expect(probe.streams.find(x => x.codec_type === 'video'))
      .toMatchObject({ codec_name: 'h264', width: 1080, height: 1920 })
    expect(probe.streams.find(x => x.codec_type === 'audio')?.codec_name).toBe('aac')
    expect(Math.abs(Number(probe.format.duration) - seconds)).toBeLessThan(1.5)
  } finally { rmSync(dir, { recursive: true, force: true }) }
}

test.describe.serial('RetailGrowthAI F2 -> F4: real signed two-shop private CPU DEV acceptance', () => {
  test('test shop A: browser login -> saved plan -> signed review -> CPU render -> private MP4', async ({ page, request }) => {
    await page.goto(cfg.frontend + '/account')
    await expect(page.getByRole('heading', { name: 'Sign in' })).toBeVisible()
    await page.getByLabel('Email').fill(cfg.a.email)
    await page.getByLabel('Password').fill(cfg.a.password)
    await page.getByRole('button', { name: 'Sign in', exact: true }).click()
    await expect(page.getByText('Signed in as ' + cfg.a.email)).toBeVisible({ timeout: 30000 })
    const token = await page.evaluate(() => {
      const raw = sessionStorage.getItem('retailgrowthai-auth-v1')
      return raw ? JSON.parse(raw).access_token : ''
    })
    expect(token.split('.')).toHaveLength(3)
    state.actorJwt = token
    const members = await membership(request, token, cfg.shopA)
    expect(members.find(x => x.shop_id === cfg.shopA)?.role).toBe('OWNER')
    expect(members.some(x => x.shop_id === cfg.shopB)).toBe(false)

    const campaign = await call(request, token, 'GET', '/campaigns/' + campaignId)
    expect(campaign.status()).toBe(200)
    const saved = await json(campaign)
    expect(saved).toMatchObject({ id: campaignId, shop_id: cfg.shopA, status: 'DRAFT' })
    expect(saved.days.some(d => d.id === dayId && d.shop_id === cfg.shopA)).toBe(true)

    const issued = await call(request, token, 'POST',
      '/campaigns/' + campaignId + '/feature4-plans', { day_id: dayId })
    expect([200, 201]).toContain(issued.status())
    const plan = await json(issued)
    expect(plan.shop_id).toBe(cfg.shopA)
    expect(plan.campaign_id).toBe(campaignId)
    expect(plan.plan_id).toMatch(UUID)
    expect(plan.proposal_sha256).toMatch(SHA)
    state.planId = plan.plan_id
    state.sourceHash = plan.proposal_sha256

    const read = await call(request, token, 'GET', '/feature4-creative-plans/' + state.planId)
    expect(read.status()).toBe(200)
    const direction = await json(read)
    expect(direction.proposal_sha256).toBe(state.sourceHash)
    expect(direction.proposal.source_feature).toBe('feature2')
    const seconds = Number(direction.proposal.duration_seconds)
    expect([15, 30, 60]).toContain(seconds)

    // The signed test-shop OWNER chooses this exact version deliberately.
    // Never emulate ROOT approval or use service_role for creative decisions.
    const reviewed = await call(request, token, 'POST',
      '/feature4-creative-plans/' + state.planId + '/review',
      { expected_source_sha256: state.sourceHash })
    expect(reviewed.status()).toBe(200)
    const approval = await json(reviewed)
    expect(approval).toMatchObject({ plan_id: state.planId, shop_id: cfg.shopA,
      status: 'APPROVED' })
    expect(approval.review_hash).toMatch(SHA)
    state.reviewHash = approval.review_hash

    const render = await call(request, token, 'POST',
      '/campaigns/' + campaignId + '/feature4-renders',
      { plan_id: state.planId, expected_review_hash: state.reviewHash })
    expect([200, 202]).toContain(render.status())
    const created = await json(render)
    expect(created.shop_id).toBe(cfg.shopA)
    expect(created.job_id).toMatch(UUID)
    state.jobId = created.job_id
    const completed = await pollHosted(async () => {
      const response = await call(request, token, 'GET', '/feature4-render-jobs/' + state.jobId)
      if (response.status() === 200) return json(response)
      const err = new Error('Feature4 job polling HTTP ' + response.status())
      err.status = response.status()
      throw err
    }, { timeoutMs: cfg.pollTimeout })
    expect(completed).toMatchObject({ job_id: state.jobId,
      shop_id: cfg.shopA, status: 'SUCCEEDED' })

    const response = await call(request, token, 'GET',
      '/feature4-render-jobs/' + state.jobId + '/download')
    expect(response.status()).toBe(200)
    const receipt = await json(response)
    expect(receipt.shop_id).toBe(cfg.shopA)
    const signed = signedDownloadUrl(receipt.url, cfg.supabase)
    const asset = await request.get(signed, { ...noRetry, maxRedirects: 0 })
    expect(asset.status()).toBe(200)
    const wire = Number(asset.headers()['content-length'])
    if (Number.isFinite(wire) && wire > 0) expect(wire).toBeLessThanOrEqual(80 * 1024 * 1024)
    privateMp4(await asset.body(), seconds)
  })

  test('test shop B: valid own login but foreign plan/review/job/download all denied', async ({ request }) => {
    expect(state.jobId && state.planId && state.reviewHash).toBeTruthy()
    const token = await login(request, cfg.b)
    const shops = await membership(request, token, cfg.shopB)
    expect(shops.some(x => x.shop_id === cfg.shopA)).toBe(false)
    for (const route of [
      '/campaigns/' + campaignId,
      '/feature4-creative-plans/' + state.planId,
      '/feature4-render-jobs/' + state.jobId,
      '/feature4-render-jobs/' + state.jobId + '/download',
    ]) denied(await call(request, token, 'GET', route))
    denied(await call(request, token, 'POST',
      '/feature4-creative-plans/' + state.planId + '/review',
      { expected_source_sha256: state.sourceHash }))
    denied(await call(request, token, 'POST',
      '/campaigns/' + campaignId + '/feature4-renders',
      { plan_id: state.planId, expected_review_hash: state.reviewHash }))
  })

  test('expired DEV token denied; repeat signed job submit remains idempotent', async ({ request }) => {
    expect(state.jobId && state.reviewHash).toBeTruthy()
    for (const [method, route, data] of [
      ['GET', '/feature4-creative-plans/' + state.planId],
      ['GET', '/feature4-render-jobs/' + state.jobId],
      ['GET', '/feature4-render-jobs/' + state.jobId + '/download'],
      ['POST', '/campaigns/' + campaignId + '/feature4-renders',
        { plan_id: state.planId, expected_review_hash: state.reviewHash }],
    ]) {
      const response = await call(request, cfg.expiredJwt, method, route, data)
      expect(response.status()).toBe(401)
    }
    const same = await call(request, state.actorJwt, 'POST',
      '/campaigns/' + campaignId + '/feature4-renders',
      { plan_id: state.planId, expected_review_hash: state.reviewHash })
    expect([200, 202]).toContain(same.status())
    expect((await json(same)).job_id).toBe(state.jobId)
  })

  test('signed owner revokes plan and completed private download fails closed', async ({ request }) => {
    const revoked = await call(request, state.actorJwt, 'POST',
      '/feature4-creative-plans/' + state.planId + '/revoke', {})
    expect(revoked.status()).toBe(200)
    expect(await json(revoked)).toMatchObject({ status: 'REVOKED', plan_id: state.planId })
    const deniedDownload = await call(request, state.actorJwt, 'GET',
      '/feature4-render-jobs/' + state.jobId + '/download')
    expect(deniedDownload.status()).toBe(404)
  })
})
