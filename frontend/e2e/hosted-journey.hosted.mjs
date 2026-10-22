// Manual and approval-gated REAL hosted DEV suite. Never imported by standard CI.
// It intentionally does not intercept network, seed fake assets, or synthesize success.
import { test, expect } from '@playwright/test'
import { spawnSync } from 'node:child_process'
import { hostedConfig, pollHosted, signedDownloadUrl } from './hosted-support.mjs'

const cfg = hostedConfig(process.env)
const state = { campaignId: '', dayId: '', jobId: '', uploadedAssetId: '', jwt: '' }
const noRetry = { failOnStatusCode: false, timeout: 30000, maxRetries: 0 }
const campaign = id => cfg.api + '/api/campaigns/' + id
const render = id => cfg.api + '/api/render-jobs/' + id

async function json(response) {
  let body
  try { body = await response.json() } catch { throw new Error('Non-JSON DEV API response, HTTP ' + response.status()) }
  return body
}
async function authed(request, token, method, url, data) {
  return request.fetch(url, { method,
    headers: { Authorization: 'Bearer ' + token, ...(data === undefined ? {} : { 'Content-Type': 'application/json' }) },
    ...(data === undefined ? {} : { data }),
    ...noRetry,
  })
}
async function loginToken(request, user) {
  const response = await request.post(cfg.supabase + '/auth/v1/token?grant_type=password', {
    headers: { apikey: cfg.publishable, 'Content-Type': 'application/json' },
    data: { email: user.email, password: user.password }, ...noRetry,
  })
  expect(response.status(), 'Separate DEV user login must succeed').toBe(200)
  const payload = await json(response)
  expect(payload.access_token).toBeTruthy()
  return payload.access_token
}
function expectDenied(response, codes) {
  expect(codes, 'Cross-tenant/expired requests must fail closed').toContain(response.status())
}
function validateMp4(bytes) {
  // ffprobe is mandatory for manual hosted qualification; media contents not stored/logged.
  const probe = spawnSync('ffprobe', ['-v', 'error', '-show_entries',
    'format=duration:stream=codec_type,codec_name,width,height', '-of', 'json', '-i', 'pipe:0'],
  { input: bytes, encoding: 'utf8', maxBuffer: 2 * 1024 * 1024, timeout: 30000 })
  if (probe.error || probe.status !== 0) {
    throw new Error('ffprobe unavailable or unable to decode signed MP4; verify local ffprobe installation')
  }
  const media = JSON.parse(probe.stdout)
  const video = media.streams.find(s => s.codec_type === 'video')
  const audio = media.streams.find(s => s.codec_type === 'audio')
  expect(video).toMatchObject({ codec_name: 'h264', width: 1080, height: 1920 })
  expect(audio?.codec_name).toBe('aac')
  expect(Number(media.format.duration)).toBeGreaterThanOrEqual(29)
  expect(Number(media.format.duration)).toBeLessThanOrEqual(31)
}

test.describe.serial('RetailGrowthAI approved hosted DEV journey (real network and private image)', () => {
  test('user A login -> real private image upload -> seven-day campaign -> PATCH draft -> 30s render -> signed MP4', async ({ page, request }) => {
    // Pin the three origin boundaries; no Playwright route mocks are installed.
    page.on('request', req => {
      const url = new URL(req.url())
      // Only enforce HTTPS for any non-document subrequests to keep browser/CDN assets observable.
      if (req.isNavigationRequest() && !cfg.allowlist.includes(url.origin)) {
        throw new Error('Unexpected DEV navigation origin')
      }
    })
    await page.goto(cfg.frontend + '/account')
    await expect(page.getByRole('heading', { name: 'Sign in' })).toBeVisible()
    await page.getByLabel('Email').fill(cfg.a.email)
    await page.getByLabel('Password').fill(cfg.a.password)
    await page.getByRole('button', { name: 'Sign in', exact: true }).click()
    await expect(page.getByText('Signed in as ' + cfg.a.email)).toBeVisible({ timeout: 30000 })
    state.jwt = await page.evaluate(() => {
      const value = sessionStorage.getItem('retailgrowthai-auth-v1')
      return value ? JSON.parse(value).access_token : ''
    })
    expect(state.jwt).toBeTruthy()
    await page.goto(cfg.frontend + '/campaigns')
    await expect(page.locator('#rg-shop')).toBeVisible()
    await page.locator('#rg-shop').selectOption(cfg.shopA)
    await page.locator('#rg-private-photo').setInputFiles(cfg.imagePath)
    await page.locator('#rg-media-evidence').fill(cfg.evidence)
    await page.getByRole('checkbox', { name: /I confirm I have commercial rights/ }).check()

    const registered = page.waitForResponse(r => r.url().includes('/rest/v1/rpc/register_uploaded_image'))
    await page.getByRole('button', { name: 'Upload image' }).click()
    const registration = await registered
    expect(registration.status(), 'Private object registration must succeed').toBe(200)
    const output = await registration.json()
    state.uploadedAssetId = typeof output === 'string' ? output : output?.id
    expect(state.uploadedAssetId).toMatch(/^[a-f0-9-]{36}$/i)
    await expect(page.getByText(/Image stored privately and registered/)).toBeVisible()
    // Check registration is actually tenant-private through the user-RLS API.
    const ownAsset = await request.get(cfg.supabase + '/rest/v1/media_assets?id=eq.' + state.uploadedAssetId +
      '&select=id,shop_id', { ...noRetry, headers: { apikey: cfg.publishable, Authorization: 'Bearer ' + state.jwt } })
    expect(ownAsset.status()).toBe(200)
    expect(await json(ownAsset)).toEqual([{ id: state.uploadedAssetId, shop_id: cfg.shopA }])

    // Uploaded media should be auto-selected; explicitly verify rather than using an old fixture.
    await expect(page.getByRole('checkbox', { name: new RegExp(state.uploadedAssetId.slice(0, 8), 'i') })).toBeChecked()
    await page.locator('#rg-start').fill(new Date(Date.now() + 86400000).toISOString().slice(0, 10))
    const submitted = page.waitForResponse(r => r.url() === cfg.api + '/api/campaigns' && r.request().method() === 'POST')
    await page.getByRole('button', { name: /Submit campaign job/ }).click()
    const created = await submitted
    expect(created.status()).toBe(202)
    const accepted = await created.json()
    expect(accepted.status).toBe('PLANNING')
    state.campaignId = accepted.campaign_id
    expect(state.campaignId).toMatch(/^[a-f0-9-]{36}$/i)
    const planned = await pollHosted(async () => {
      const response = await authed(request, state.jwt, 'GET', campaign(state.campaignId))
      if (response.status() === 200) return json(response)
      const err = new Error('DEV campaign polling HTTP ' + response.status())
      err.status = response.status()
      throw err
    }, { timeoutMs: cfg.pollTimeout })
    expect(planned).toMatchObject({ shop_id: cfg.shopA, status: 'DRAFT' })
    expect(planned.days).toHaveLength(7)
    expect(planned.days.every(d => d.shop_id === cfg.shopA)).toBe(true)
    state.dayId = planned.days[0].id
    await expect(page.getByText('Authenticated campaign draft loaded. Publishing is still unavailable.'))
      .toBeVisible({ timeout: 30000 })
    const edited = 'Hosted DEV approved E2E draft edit ' + new Date().toISOString()
    await page.getByLabel('Post body').fill(edited)
    await expect(page.getByRole('button', { name: 'Render saved Reel' })).toBeDisabled()
    const patched = page.waitForResponse(r => r.url() === campaign(state.campaignId) +
      '/days/' + state.dayId && r.request().method() === 'PATCH')
    await page.getByRole('button', { name: 'Save day' }).click()
    expect((await patched).status()).toBe(200)
    await expect(page.getByText('Draft day saved to your secure workspace.')).toBeVisible()
    const persistedResponse = await authed(request, state.jwt, 'GET', campaign(state.campaignId))
    expect(persistedResponse.status()).toBe(200)
    const persisted = await json(persistedResponse)
    expect(persisted.days.find(d => d.id === state.dayId)?.linkedin?.post_text).toBe(edited)

    const createdRender = page.waitForResponse(r => r.url() === campaign(state.campaignId) +
      '/renders' && r.request().method() === 'POST')
    await page.getByRole('button', { name: 'Render saved Reel' }).click()
    const renderResponse = await createdRender
    expect([200, 202]).toContain(renderResponse.status())
    const queued = await renderResponse.json()
    state.jobId = queued.job_id
    expect(state.jobId).toMatch(/^[a-f0-9-]{36}$/i)
    // Read-only polling tolerates bounded transient 429/503 but never re-enqueues.
    const ready = await pollHosted(async () => {
      const response = await authed(request, state.jwt, 'GET', render(state.jobId))
      if (response.status() === 200) return json(response)
      const err = new Error('DEV render polling HTTP ' + response.status())
      err.status = response.status()
      throw err
    }, { timeoutMs: cfg.pollTimeout })
    expect(ready).toMatchObject({ job_id: state.jobId, status: 'SUCCEEDED' })
    expect(ready.output_asset_id).toBeTruthy()
    const downloadResponse = await authed(request, state.jwt, 'GET', render(state.jobId) + '/download')
    expect(downloadResponse.status()).toBe(200)
    const signed = signedDownloadUrl((await json(downloadResponse)).url, cfg.supabase)
    const asset = await request.get(signed, { ...noRetry, maxRedirects: 0 })
    expect(asset.status()).toBe(200)
    expect(asset.headers()['content-type']).toMatch(/video\/mp4|application\/octet-stream/)
    const bytes = await asset.body()
    expect(bytes.length).toBeGreaterThan(10000)
    validateMp4(bytes)
  })

  test('user B cannot read, modify, render or download user A resources', async ({ request }) => {
    expect(state.campaignId && state.dayId && state.jobId && state.uploadedAssetId).toBeTruthy()
    const token = await loginToken(request, cfg.b)
    const deniedRead = await authed(request, token, 'GET', campaign(state.campaignId))
    expectDenied(deniedRead, [403, 404])
    const deniedEdit = await authed(request, token, 'PATCH',
      campaign(state.campaignId) + '/days/' + state.dayId,
      { topic: 'cross-tenant edit', linkedin: { post_text: 'hijack', hashtags: [] }, instagram: {} })
    expectDenied(deniedEdit, [403, 404])
    const deniedRender = await authed(request, token, 'POST', campaign(state.campaignId) + '/renders',
      { day_id: state.dayId, preset: 'instagram_reel_30s' })
    expectDenied(deniedRender, [403, 404])
    for (const suffix of ['', '/download']) {
      expectDenied(await authed(request, token, 'GET', render(state.jobId) + suffix), [403, 404])
    }
    const foreignMedia = await request.get(cfg.supabase + '/rest/v1/media_assets?id=eq.' +
      state.uploadedAssetId + '&select=id', {
      ...noRetry, headers: { apikey: cfg.publishable, Authorization: 'Bearer ' + token },
    })
    expect(foreignMedia.status()).toBe(200)
    expect(await json(foreignMedia)).toEqual([])
  })

  test('genuinely expired DEV JWT is denied by API for every resource operation', async ({ request }) => {
    const expired = cfg.expiredJwt
    const plan = await authed(request, expired, 'POST', cfg.api + '/api/campaigns', {
      shop_id: cfg.shopA, brief: 'Unauthorized expired token E2E',
      duration_days: 7, start_date: '2026-12-01', timezone: 'Asia/Kolkata',
      language: 'en-IN', platforms: ['linkedin', 'instagram'],
      media_asset_ids: [state.uploadedAssetId], offer: null,
    })
    expectDenied(plan, [401])
    for (const [method, url, data] of [
      ['GET', campaign(state.campaignId)],
      ['PATCH', campaign(state.campaignId) + '/days/' + state.dayId, { topic: 'forged change' }],
      ['POST', campaign(state.campaignId) + '/renders', { day_id: state.dayId, preset: 'instagram_reel_30s' }],
      ['GET', render(state.jobId)],
      ['GET', render(state.jobId) + '/download'],
    ]) {
      expectDenied(await authed(request, expired, method, url, data), [401])
    }
  })

  test('render re-submission is idempotent; optional fault-injected retry recovery is inspected', async ({ request }) => {
    const resubmit = await authed(request, state.jwt, 'POST',
      campaign(state.campaignId) + '/renders',
      { day_id: state.dayId, preset: 'instagram_reel_30s' })
    expect([200, 202]).toContain(resubmit.status())
    const same = await json(resubmit)
    expect(same.job_id).toBe(state.jobId)

    test.skip(!cfg.recoveryJob,
      'No explicitly pre-faulted DEV job provided. Azure poison/reconciler retry recovery remains UNVERIFIED.')
    // Operator must create a DEV-only, safely fault-injected job and record the
    // source event/attempt count independently (there is no public retry API).
    const recovered = await pollHosted(async () => {
      const response = await authed(request, state.jwt, 'GET', render(cfg.recoveryJob))
      if (response.status() === 200) return json(response)
      const err = new Error('Recovery job HTTP ' + response.status())
      err.status = response.status()
      throw err
    }, { timeoutMs: cfg.pollTimeout })
    expect(recovered).toMatchObject({ job_id: cfg.recoveryJob, status: 'SUCCEEDED' })
  })
})
