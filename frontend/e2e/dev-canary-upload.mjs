// Explicit opt-in: invoked only by the one-time DEV canary after a freshly
// approved temporary retailer and shop have been created. Not a CI spec.
// Only original locally generated PNG bytes can enter the file picker.
import { chromium, expect } from '@playwright/test'
import { readFileSync } from 'node:fs'

const DEV_HOST = 'https://purple-dune-06b5da200.2.azurestaticapps.net'
const SUPABASE = 'https://jeearzffnjbvghwjjjrf.supabase.co'
const SHOP = process.env.RGAI_BROWSER_SHOP_ID || ''
const EMAIL = process.env.RGAI_BROWSER_USER_EMAIL || ''
const PASSWORD = process.env.RGAI_BROWSER_USER_PASSWORD || ''
const PNG_PATH = process.env.RGAI_BROWSER_PNG_PATH || ''
const APPROVAL = process.env.RGAI_DEV_CANARY_APPROVAL || ''
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i
let stage = 'config'
let browser

async function main() {
  if (APPROVAL !== 'AUTHORIZED_RETAILGROWTHAI_DEV_ONLY' ||
      process.env.RGAI_DEV_PLAYWRIGHT_UPLOAD !== '1' ||
      !UUID.test(SHOP) || !EMAIL.endsWith('@example.invalid') ||
      !EMAIL.startsWith('rgai-canary-') || PASSWORD.length < 24) {
    throw new Error('guard')
  }
  const image = readFileSync(PNG_PATH)
  if (image.length < 100 || image.length > 25 * 1024 * 1024 ||
      !image.subarray(0, 8).equals(Buffer.from('89504e470d0a1a0a', 'hex'))) {
    throw new Error('fixture')
  }
  stage = 'launch'
  browser = await chromium.launch({ headless: true })
  const context = await browser.newContext({ acceptDownloads: false, serviceWorkers: 'block' })
  const page = await context.newPage()
  // Record only the shop-scoped Storage path, never JWT, payload bytes or query tokens.
  let objectPath = ''
  page.on('request', req => {
    const url = new URL(req.url())
    const prefix = '/storage/v1/object/retailgrowth-media/'
    if (req.method() === 'POST' && url.origin === SUPABASE && url.pathname.startsWith(prefix)) {
      const path = decodeURIComponent(url.pathname.slice(prefix.length))
      if (path.startsWith(SHOP + '/uploads/')) objectPath = path
    }
  })
  stage = 'signin'
  await page.goto(DEV_HOST + '/account', { waitUntil: 'domcontentloaded' })
  await page.getByLabel('Email', { exact: true }).fill(EMAIL)
  await page.getByLabel('Password', { exact: true }).fill(PASSWORD)
  await page.getByRole('button', { name: 'Sign in', exact: true }).click()
  await expect(page.getByText('Signed in as ' + EMAIL)).toBeVisible({ timeout: 30000 })

  stage = 'select-shop'
  await page.goto(DEV_HOST + '/campaigns', { waitUntil: 'domcontentloaded' })
  await expect(page.locator('#rg-shop')).toBeVisible({ timeout: 30000 })
  await page.locator('#rg-shop').selectOption(SHOP)
  await expect(page.locator('#rg-private-photo')).toBeVisible()

  stage = 'upload'
  await page.locator('#rg-private-photo').setInputFiles({
    name: 'retailgrowthai-original-dev-test.png',
    mimeType: 'image/png',
    buffer: image,
  })
  await page.locator('#rg-license-type').selectOption('owned')
  await page.locator('#rg-media-evidence').fill(
    'Original unbranded synthetic PNG generated in RetailGrowthAI DEV canary; no third-party rights involved.')
  await page.getByRole('checkbox', { name: /I confirm I have commercial rights/ }).check()
  // Exactly one binary POST and one registration request; no blind mutation retry.
  const responsePromise = page.waitForResponse(response =>
    response.url() === SUPABASE + '/rest/v1/rpc/register_uploaded_image' &&
    response.request().method() === 'POST', { timeout: 60000 })
  await page.getByRole('button', { name: 'Upload image' }).click()
  const response = await responsePromise
  if (response.status() !== 200) throw new Error('registration')
  const body = await response.json()
  const id = typeof body === 'string' ? body : body?.id
  if (!UUID.test(id) || !new RegExp('^' + SHOP + '/uploads/[0-9a-f-]{36}\\.png$', 'i').test(objectPath)) {
    throw new Error('result')
  }
  await expect(page.getByText(/Image stored privately and registered/)).toBeVisible()
  // Return only a UUID and a tenant-scoped test path for bounded server-side cleanup.
  console.log('CANARY_PLAYWRIGHT_UPLOAD=' + JSON.stringify({
    asset_id: id, object_path: objectPath,
  }))
  await context.close()
}
try {
  await main()
} catch {
  // Never leak credentials, tokens, private response bodies, or page snapshots.
  console.error('CANARY_PLAYWRIGHT_FAILED_STAGE=' + stage)
  process.exitCode = 1
} finally {
  if (browser) await browser.close()
}
