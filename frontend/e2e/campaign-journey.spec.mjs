import { test, expect } from '@playwright/test'
import { readFileSync } from 'node:fs'

const fixture = JSON.parse(readFileSync(new URL('../src/features/campaigns/fixtures/sample-campaign.json', import.meta.url), 'utf8'))
const SHOP = 'b1000000-0000-4000-8000-000000000001'
const FOREIGN_SHOP = 'b2000000-0000-4000-8000-000000000001'
const MEDIA = 'a1000000-0000-4000-8000-000000000001'
const UPLOADED = 'a9000000-0000-4000-8000-000000000001'
const CAMPAIGN = 'c9000000-0000-4000-8000-000000000001'
const JOB = 'e9000000-0000-4000-8000-000000000001'
const USER = 'f9000000-0000-4000-8000-000000000001'
const SIGNED = 'https://e2e.supabase.test/storage/v1/object/sign/retailgrowth-media/' + SHOP + '/renders/' + JOB + '.mp4?token=offline-fixture'
const SUPABASE = 'https://e2e.supabase.test'
const BACKEND = 'https://api.e2e.retailgrowth.test'

function payload(status, body, route) {
  return route.fulfill({
    status,
    contentType: 'application/json',
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PATCH, OPTIONS',
      'Access-Control-Allow-Headers': 'apikey, authorization, content-type, x-upsert, prefer',
    },
    body: JSON.stringify(body),
  })
}

function normalizedCampaign() {
  return {
    ...structuredClone(fixture),
    id: CAMPAIGN,
    shop_id: SHOP,
    status: 'DRAFT',
    days: fixture.days.map(day => structuredClone({
      ...day, shop_id: SHOP, campaign_id: CAMPAIGN,
    })),
  }
}

/** Intercept every external origin: real UI/client, offline-only HTTP mocks. */
async function mockServices(page, options = {}) {
  const state = {
    sessions: 0, uploads: [], registrations: [], requests: [], saves: [],
    renders: [], renderPolls: 0, signedOpens: 0, campaign: normalizedCampaign(),
    assets: options.emptyAssets ? [] : [{
      id: MEDIA, shop_id: SHOP, license_name: 'owned',
      mime_type: 'image/png', source: 'UPLOAD',
    }],
  }
  const allow = { 'Access-Control-Allow-Origin': '*' }
  await page.context().route(SUPABASE + '/storage/v1/object/sign/**', async route => {
    state.signedOpens++
    await route.fulfill({
      status: 200, contentType: 'video/mp4',
      headers: { ...allow, 'Content-Disposition': 'inline' },
      body: Buffer.from('offline-stub-not-a-real-mp4'),
    })
  })
  await page.route(SUPABASE + '/**', async route => {
    const req = route.request()
    const url = new URL(req.url())
    const path = url.pathname
    const method = req.method()
    if (method === 'OPTIONS') return payload(204, null, route)
    if (path === '/auth/v1/token' && url.searchParams.get('grant_type') === 'password') {
      state.sessions++
      return options.invalidLogin
        ? payload(400, { error_description: 'Invalid login credentials' }, route)
        : payload(200, { access_token: 'test-alice-token', refresh_token: 'test-refresh',
          expires_in: 3600, user: { id: USER, email: 'owner@example.test' } }, route)
    }
    if (path === '/auth/v1/user') {
      return req.headers().authorization === 'Bearer test-alice-token'
        ? payload(200, { id: USER, email: 'owner@example.test' }, route)
        : payload(401, { error: 'Invalid session' }, route)
    }
    if (path === '/auth/v1/token' && url.searchParams.get('grant_type') === 'refresh_token') {
      return payload(401, { error_description: 'Refresh token expired' }, route)
    }
    if (path === '/auth/v1/logout') return payload(204, null, route)
    if (path === '/rest/v1/shop_memberships') return payload(200, [
      { shop_id: SHOP, role: options.viewer ? 'VIEWER' : 'OWNER', active: true },
    ], route)
    if (path === '/rest/v1/shops') return payload(200, [
      { id: SHOP, name: 'Boutique A', slug: 'boutique-a', owner_user_id: USER, timezone: 'Asia/Kolkata' },
    ], route)
    if (path === '/rest/v1/business_profiles') return payload(200, [], route)
    if (path === '/rest/v1/media_assets') return payload(200, state.assets, route)
    if (path.startsWith('/storage/v1/object/retailgrowth-media/')) {
      state.uploads.push({
        path, headers: req.headers(), bytes: req.postDataBuffer(),
      })
      return payload(options.uploadDenied ? 403 : 200, options.uploadDenied
        ? { error: 'STORAGE_FORBIDDEN' } : { Key: path }, route)
    }
    if (path === '/rest/v1/rpc/register_uploaded_image') {
      const data = req.postDataJSON()
      state.registrations.push(data)
      if (options.registrationDenied) return payload(403, { error: 'FORBIDDEN' }, route)
      state.assets.push({
        id: UPLOADED, shop_id: SHOP, license_name: data.p_license_name,
        mime_type: 'image/png', source: 'UPLOAD',
      })
      return payload(200, UPLOADED, route)
    }
    throw new Error('Unexpected Supabase request: ' + method + ' ' + path)
  })

  await page.route(BACKEND + '/**', async route => {
    const req = route.request()
    const path = new URL(req.url()).pathname
    const method = req.method()
    if (method === 'OPTIONS') return payload(204, null, route)
    const authorization = req.headers().authorization
    if (authorization !== 'Bearer test-alice-token') {
      return payload(401, { error: 'UNAUTHORIZED' }, route)
    }
    if (method === 'POST' && path === '/api/campaigns') {
      const body = req.postDataJSON()
      state.requests.push({ body, authorization })
      if (options.campaignDenied || body.shop_id !== SHOP ||
          body.media_asset_ids.some(id => !state.assets.some(asset => asset.id === id))) {
        return payload(403, { error: 'FORBIDDEN' }, route)
      }
      return payload(202, { campaign_id: CAMPAIGN, status: 'PLANNING' }, route)
    }
    if (method === 'GET' && path === '/api/campaigns/' + CAMPAIGN) {
      return payload(200, options.foreignDraft
        ? { ...state.campaign, shop_id: FOREIGN_SHOP } : state.campaign, route)
    }
    if (method === 'PATCH' && path.startsWith('/api/campaigns/' + CAMPAIGN + '/days/')) {
      const body = req.postDataJSON()
      state.saves.push({ body, authorization })
      if (options.conflict) return payload(409, { error: 'EDIT_CONFLICT' }, route)
      const day = state.campaign.days.find(item => path.endsWith('/' + item.id))
      if (!day) return payload(404, { error: 'NOT_FOUND' }, route)
      Object.assign(day, body)
      return payload(200, { day }, route)
    }
    if (method === 'POST' && path === '/api/campaigns/' + CAMPAIGN + '/renders') {
      state.renders.push(req.postDataJSON())
      if (options.renderDenied) return payload(403, { error: 'ASSET_RIGHTS_UNVERIFIED' }, route)
      return payload(202, { job_id: JOB, status: 'QUEUED' }, route)
    }
    if (method === 'GET' && path === '/api/render-jobs/' + JOB) {
      state.renderPolls++
      return payload(200, {
        job_id: JOB, status: options.renderFailed ? 'FAILED' : 'SUCCEEDED',
        output_asset_id: options.renderFailed ? null : 'a9000000-0000-4000-8000-000000000002',
        error_code: options.renderFailed ? 'RENDER_FAILED' : null,
      }, route)
    }
    if (method === 'GET' && path === '/api/render-jobs/' + JOB + '/download') {
      return options.unsafeDownload
        ? payload(200, { url: 'https://attacker.example/steal.mp4' }, route)
        : payload(200, { url: SIGNED }, route)
    }
    throw new Error('Unexpected backend request: ' + method + ' ' + path)
  })
  return state
}

async function login(page) {
  await page.goto('/account')
  await page.getByLabel('Email').fill('owner@example.test')
  await page.getByLabel('Password').fill('only-a-test-password')
  await page.getByRole('button', { name: 'Sign in', exact: true }).click()
  await expect(page.getByText('Signed in as owner@example.test')).toBeVisible()
}

async function business(page) {
  await page.goto('/campaigns')
  await page.locator('#rg-shop').selectOption(SHOP)
}

async function submit(page) {
  await expect(page.getByRole('checkbox', { name: /image\/png.*owned/ })).toBeVisible()
  await page.getByRole('checkbox', { name: /image\/png.*owned/ }).check()
  await page.getByRole('button', { name: /Submit campaign job/ }).click()
}

async function loaded(page) {
  await expect(page.getByText('Authenticated campaign draft loaded · Not scheduled or published.')).toBeVisible()
}

test('real UI: login -> authorized seven-day plan -> edit/save -> render status -> signed link', async ({ page }) => {
  const state = await mockServices(page)
  await login(page)
  await business(page)
  await submit(page)
  await loaded(page)
  expect(state.requests).toHaveLength(1)
  expect(state.requests[0].authorization).toBe('Bearer test-alice-token')
  expect(state.requests[0].body).toMatchObject({
    shop_id: SHOP, duration_days: 7, media_asset_ids: [MEDIA],
  })
  await expect(page.locator('.rg-calendar-day')).toHaveCount(7)

  await page.getByLabel('Post body').fill('Owner-edited description approved in the mock workspace')
  await expect(page.getByRole('button', { name: 'Render saved Reel' })).toBeDisabled()
  await page.getByRole('button', { name: 'Save day' }).click()
  await expect(page.getByText('Draft day saved to your secure workspace.')).toBeVisible()
  expect(state.saves).toHaveLength(1)
  expect(Object.keys(state.saves[0].body).sort()).toEqual(['instagram', 'linkedin', 'topic'])
  expect(state.saves[0].body.linkedin.post_text).toContain('Owner-edited')

  await page.getByRole('button', { name: 'Render saved Reel' }).click()
  expect(state.renders).toEqual([{
    day_id: fixture.days[0].id, preset: 'instagram_reel_30s',
  }])
  await expect.poll(() => state.renderPolls, { timeout: 12_000 }).toBeGreaterThan(0)
  await expect(page.getByRole('button', { name: 'Download signed MP4' })).toBeEnabled()
  await page.getByRole('button', { name: 'Download signed MP4' }).click()
  await expect.poll(() => state.signedOpens).toBeGreaterThan(0)
})

test('browser validates commercial rights and uploads binary before restricted registration', async ({ page }) => {
  const state = await mockServices(page, { emptyAssets: true })
  await login(page)
  await business(page)
  const bytes = Buffer.alloc(128, 9)
  Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]).copy(bytes)
  await page.locator('#rg-private-photo').setInputFiles({
    name: 'owned-photo.png', mimeType: 'image/png', buffer: bytes,
  })
  await page.locator('#rg-media-evidence').fill('Original product photography owned by our boutique')
  await expect(page.getByRole('button', { name: 'Upload image' })).toBeDisabled()
  await page.getByRole('checkbox', { name: /I confirm I have commercial rights/ }).check()
  await page.getByRole('button', { name: 'Upload image' }).click()
  await expect(page.getByText(/Image stored privately and registered/)).toBeVisible()
  expect(state.uploads).toHaveLength(1)
  expect(state.uploads[0].path).toMatch(/^\/storage\/v1\/object\/retailgrowth-media\/b100.*\/uploads\/[0-9a-f-]+\.png$/)
  expect(state.uploads[0].headers.authorization).toBe('Bearer test-alice-token')
  expect(state.uploads[0].bytes.subarray(0, 8)).toEqual(bytes.subarray(0, 8))
  expect(state.registrations[0]).toMatchObject({
    p_shop_id: SHOP, p_license_name: 'owned',
    p_attribution: 'Original product photography owned by our boutique',
  })
  await page.getByRole('button', { name: /Submit campaign job/ }).click()
  await loaded(page)
  expect(state.requests[0].body.media_asset_ids).toContain(UPLOADED)
})

test('invalid login, viewer permissions and cross-tenant creation fail closed', async ({ page }) => {
  const state = await mockServices(page, { invalidLogin: true })
  await page.goto('/account')
  await page.getByLabel('Email').fill('owner@example.test')
  await page.getByLabel('Password').fill('wrong-password')
  await page.getByRole('button', { name: 'Sign in', exact: true }).click()
  await expect(page.getByRole('alert')).toContainText('Invalid login credentials')
  expect(state.requests).toHaveLength(0)
})

test('viewer cannot select a business for a live campaign', async ({ page }) => {
  const state = await mockServices(page, { viewer: true })
  await login(page)
  await page.goto('/campaigns')
  await expect(page.locator('#rg-shop option')).toHaveCount(1)
  await page.getByRole('button', { name: /Preview campaign request/ }).click()
  expect(state.requests).toHaveLength(0)
  await expect(page.getByText(/No campaign was generated/)).toBeVisible()
})

test('API cross-tenant denial and response tenant mismatch cannot load a draft', async ({ page }) => {
  const state = await mockServices(page, { campaignDenied: true })
  await login(page)
  await business(page)
  await submit(page)
  await expect(page.getByRole('alert')).toContainText('FORBIDDEN')
  expect(state.requests).toHaveLength(1)
  await expect(page.getByRole('button', { name: 'Render Reel · unavailable' })).toBeDisabled()
})

test('foreign-tenant GET response is rejected by the client', async ({ page }) => {
  const state = await mockServices(page, { foreignDraft: true })
  await login(page)
  await business(page)
  await submit(page)
  await expect(page.getByRole('alert')).toContainText('Campaign tenant mismatch')
  expect(state.requests).toHaveLength(1)
  await expect(page.getByRole('button', { name: 'Save day' })).toHaveCount(0)
})

test('failed upload registration, edit conflict and unsafe download surface failures', async ({ page }) => {
  const state = await mockServices(page, { registrationDenied: true, conflict: true })
  await login(page)
  await business(page)
  const bytes = Buffer.alloc(128, 9)
  Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]).copy(bytes)
  await page.locator('#rg-private-photo').setInputFiles({
    name: 'uploaded.png', mimeType: 'image/png', buffer: bytes,
  })
  await page.locator('#rg-media-evidence').fill('Original product photograph owned by our store')
  await page.getByRole('checkbox', { name: /I confirm I have commercial rights/ }).check()
  await page.getByRole('button', { name: 'Upload image' }).click()
  await expect(page.getByRole('alert')).toContainText('FORBIDDEN')
  expect(state.registrations).toHaveLength(1)

  await submit(page)
  await loaded(page)
  await page.getByLabel('Post body').fill('Conflicting local edit')
  await page.getByRole('button', { name: 'Save day' }).click()
  await expect(page.getByRole('alert')).toContainText('Reload before trying again')
  await expect(page.getByRole('button', { name: 'Render saved Reel' })).toBeDisabled()
})

test('failed render never provides a signed download', async ({ page }) => {
  const state = await mockServices(page, { renderFailed: true })
  await login(page)
  await business(page)
  await submit(page)
  await loaded(page)
  await page.getByRole('button', { name: 'Render saved Reel' }).click()
  await expect.poll(() => state.renderPolls, { timeout: 12_000 }).toBeGreaterThan(0)
  await expect(page.getByRole('button', { name: 'Download signed MP4' })).toBeDisabled()
  expect(state.signedOpens).toBe(0)
})

test('unsigned external download URL is never opened', async ({ page }) => {
  const state = await mockServices(page, { unsafeDownload: true })
  await login(page)
  await business(page)
  await submit(page)
  await loaded(page)
  await page.getByRole('button', { name: 'Render saved Reel' }).click()
  await expect.poll(() => state.renderPolls, { timeout: 12_000 }).toBeGreaterThan(0)
  await page.getByRole('button', { name: 'Download signed MP4' }).click()
  await expect(page.getByRole('alert')).toContainText('private storage')
  expect(state.signedOpens).toBe(0)
})
