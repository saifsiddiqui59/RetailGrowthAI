import { test, expect } from '@playwright/test'

const SUPABASE = 'https://e2e.supabase.test'
const API = 'https://api.e2e.retailgrowth.test'
const SHOP = 'a1000000-0000-4000-8000-000000000001'
const USER = 'a9000000-0000-4000-8000-000000000001'
const DAY = 'a2000000-0000-4000-8000-000000000001'
const ACCOUNT = 'a3000000-0000-4000-8000-000000000001'
const JOB = 'a4000000-0000-4000-8000-000000000001'

function reply(route, body, status = 200) {
  return route.fulfill({ status, contentType: 'application/json',
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Headers': 'authorization, content-type, apikey',
      'Access-Control-Allow-Methods': 'OPTIONS, GET, POST',
    }, body: JSON.stringify(body) })
}

async function mockSocial(page, { role = 'OWNER', quotaDenied = false } = {}) {
  const state = { writes: [], jobs: [], external: [] }
  page.on('request', request => {
    const host = new URL(request.url()).hostname
    if (!['127.0.0.1', 'e2e.supabase.test', 'api.e2e.retailgrowth.test'].includes(host)) {
      state.external.push(request.url())
    }
  })
  await page.route(SUPABASE + '/**', route => {
    const req = route.request()
    const path = new URL(req.url()).pathname
    if (req.method() === 'OPTIONS') return reply(route, {})
    if (path === '/auth/v1/user') return reply(route, { id: USER, email: 'mock-owner@example.invalid' })
    if (path === '/rest/v1/rpc/retail_platform_me') return reply(route, false)
    if (path === '/rest/v1/shop_memberships') return reply(route, [{
      shop_id: SHOP, active: true, role,
    }])
    if (path === '/rest/v1/shops') return reply(route, [{
      id: SHOP, name: 'Mock Shop', slug: 'mock-shop', timezone: 'Asia/Kolkata',
      owner_user_id: USER,
    }])
    throw new Error('Unexpected mock Supabase request ' + req.method() + ' ' + path)
  })
  await page.route(API + '/**', route => {
    const req = route.request()
    const u = new URL(req.url())
    const path = u.pathname
    const method = req.method()
    if (method === 'OPTIONS') return reply(route, {})
    if (req.headers().authorization !== 'Bearer offline-social-user-jwt') {
      return reply(route, { error: 'UNAUTHORIZED' }, 401)
    }
    if (method === 'GET') {
      if (u.searchParams.get('shop_id') !== SHOP) return reply(route, { error: 'FORBIDDEN' }, 403)
      if (path === '/api/social/accounts') return reply(route, { accounts: [{
        id: ACCOUNT, shop_id: SHOP, provider: 'linkedin',
        display_name: 'Mock Member', connection_status: 'CONNECTED',
      }] })
      if (path === '/api/social/days') return reply(route, { days: [{
        id: DAY, shop_id: SHOP, scheduled_date: '2027-02-01',
        topic: 'Mock special offer', review_status: 'APPROVED',
        linkedin: { post_text: 'Review this offer before publication' },
      }] })
      if (path === '/api/social/jobs') return reply(route, { jobs: [...state.jobs] })
    }
    if (method !== 'POST' || !path.startsWith('/api/social/jobs/')) {
      throw new Error('Unexpected social request ' + method + ' ' + path)
    }
    const body = req.postDataJSON()
    state.writes.push({ path, body, authorization: req.headers().authorization })
    if (role === 'VIEWER' || body.shop_id !== SHOP) return reply(route, { error: 'FORBIDDEN' }, 403)
    if (path === '/api/social/jobs/create') {
      const job = { id: JOB, shop_id: SHOP, social_account_id: ACCOUNT,
        campaign_day_id: DAY, provider: 'linkedin', caption: body.caption,
        scheduled_at: '2027-02-01T04:30:00Z', timezone: 'Asia/Kolkata',
        status: 'DRAFT', revision: 1 }
      state.jobs.push(job)
      return reply(route, { id: JOB, revision: 1, status: 'DRAFT' }, 201)
    }
    const job = state.jobs.find(j => j.id === body.job_id)
    if (!job || body.revision !== job.revision) {
      return reply(route, { error: 'REVIEWED_CONTENT_CHANGED' }, 409)
    }
    if (path === '/api/social/jobs/revise') {
      if (job.status !== 'DRAFT') return reply(route, { error: 'REVIEWED_CONTENT_CHANGED' }, 409)
      job.caption = body.caption
      job.revision++
      job.scheduled_at = '2027-02-02T05:00:00Z'
      return reply(route, { id: JOB, revision: job.revision, status: 'DRAFT' })
    }
    if (path === '/api/social/jobs/approve') {
      if (quotaDenied) return reply(route, { error: 'PUBLISH_QUOTA_EXCEEDED' }, 429)
      if (job.status !== 'DRAFT') return reply(route, { error: 'REVIEWED_CONTENT_CHANGED' }, 409)
      job.status = 'APPROVED'
      return reply(route, { id: JOB, revision: job.revision, status: 'APPROVED' })
    }
    if (path === '/api/social/jobs/cancel') {
      job.status = 'CANCELED'
      return reply(route, { id: JOB, status: 'CANCELED' })
    }
    throw new Error('Unexpected social mutation ' + path)
  })
  await page.addInitScript(() => {
    sessionStorage.setItem('retailgrowthai-auth-v1', JSON.stringify({
      access_token: 'offline-social-user-jwt',
      refresh_token: 'offline-social-refresh',
      expires_at: 2000000000,
    }))
  })
  return state
}

async function draft(page) {
  await expect(page.getByRole('heading', { name: 'Review and schedule posts' })).toBeVisible()
  await page.locator('#social-authoring-day').selectOption(DAY)
  await page.locator('#social-authoring-account').selectOption(ACCOUNT)
  await page.locator('#social-authoring-date').fill('2027-02-01')
  await page.getByRole('button', { name: 'Save publishing draft' }).click()
  await expect(page.getByText('Review this offer before publication')).toBeVisible()
}

test('mock-only retailer creates, revises, explicitly re-reviews, approves; no provider call', async ({ page }) => {
  const state = await mockSocial(page)
  await page.goto('/social')
  await draft(page)
  await expect(page.getByRole('button', { name: 'Approve and reserve publishing quota' })).toBeDisabled()
  await page.getByRole('button', { name: 'Edit draft / reschedule' }).click()
  await page.locator('#social-revise-caption-' + JOB).fill('Revised and checked sale copy')
  await page.locator('#social-revise-date-' + JOB).fill('2027-02-02')
  await page.locator('#social-revise-time-' + JOB).fill('10:30')
  await page.getByRole('button', { name: 'Save revised draft' }).click()
  await expect(page.getByText('Revised and checked sale copy')).toBeVisible()
  expect(state.jobs[0].revision).toBe(2)
  await page.getByRole('checkbox', { name: /reviewed this exact text/ }).check()
  await page.getByRole('button', { name: 'Approve and reserve publishing quota' }).click()
  await expect(page.getByText('linkedin · APPROVED')).toBeVisible()
  const edits = state.writes.filter(w => w.path.endsWith('/revise'))
  const approvals = state.writes.filter(w => w.path.endsWith('/approve'))
  expect(edits).toHaveLength(1)
  expect(edits[0].body.revision).toBe(1)
  expect(approvals).toHaveLength(1)
  expect(approvals[0].body.revision).toBe(2)
  expect(state.writes.every(w => w.authorization === 'Bearer offline-social-user-jwt')).toBe(true)
  expect(state.external).toEqual([])
})

test('quota denial remains visible and viewer never gets browser authoring controls', async ({ page }) => {
  const state = await mockSocial(page, { quotaDenied: true })
  await page.goto('/social')
  await draft(page)
  await page.getByRole('checkbox', { name: /reviewed this exact text/ }).check()
  await page.getByRole('button', { name: 'Approve and reserve publishing quota' }).click()
  await expect(page.getByRole('alert')).toContainText('publishing quota')
  expect(state.jobs[0].status).toBe('DRAFT')
  await page.getByRole('button', { name: 'Cancel unsent job' }).click()
  await expect(page.getByText('linkedin · DRAFT')).toHaveCount(0)
  expect(state.writes.filter(w => w.path.endsWith('/cancel'))).toHaveLength(1)

  // Fresh isolated browser context cannot inherit the owner's JWT.
  const viewer = await page.context().newPage()
  const viewerState = await mockSocial(viewer, { role: 'VIEWER' })
  await viewer.goto('/social')
  await expect(viewer.getByText('A business OWNER or EDITOR is required')).toBeVisible()
  await expect(viewer.getByRole('button', { name: 'Save publishing draft' })).toBeDisabled()
  expect(viewerState.writes).toHaveLength(0)
  await viewer.close()
})
