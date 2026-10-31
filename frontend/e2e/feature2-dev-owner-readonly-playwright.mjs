#!/usr/bin/env node
/**
 * RetailGrowthAI-only authenticated hosted Playwright smoke (non-CI, read-only).
 *
 * NO USER PASSWORD ENV OR STORED AUTH JSON REQUIRED.
 * --plan: zero network; safe for CI unit test.
 * --run: opt-in headed Chromium; human signs in via the actual DEV login page.
 *
 * This test intentionally does not reuse a third-party browser-agent profile:
 * Playwright cannot safely extract cookies or storage from that profile.
 * It never creates campaigns, imports assets, approves rights or queues renders.
 */
const HOST = 'https://purple-dune-06b5da200.2.azurestaticapps.net'
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i
const flags = process.argv.slice(2)

if (flags.length !== 1 || !['--plan', '--run'].includes(flags[0])) {
  console.error('Usage: node feature2-dev-owner-readonly-playwright.mjs --plan|--run')
  process.exit(2)
}
const plan = {
  mode: 'HOSTED_DEV_AUTHENTICATED_READONLY',
  frontend: HOST,
  needs_password_in_chat: false,
  needs_permanent_auth_file: false,
  playwright_uses_saved_browser_agent_profile: false,
  no_uploads: true,
  no_paid_ai: true,
  no_render_or_publish: true,
  routes: ['/account', '/campaigns', '/trends'],
}
if (flags[0] === '--plan') {
  console.log(JSON.stringify(plan))
  process.exit(0)
}
if (process.env.CI || process.env.GITHUB_ACTIONS ||
    process.env.RGAI_DEV_READONLY_APPROVAL !== 'I_APPROVE_RETAILGROWTHAI_DEV_OWNER_READONLY') {
  console.error('BLOCKED: explicit local DEV-only authorization required; CI/Actions prohibited')
  process.exit(3)
}
const expectedShop = (process.env.RGAI_DEV_TEST_SHOP_ID || '').trim()
if (!UUID.test(expectedShop)) {
  console.error('BLOCKED: set RGAI_DEV_TEST_SHOP_ID to the existing authorized test shop UUID')
  process.exit(3)
}

// Load browser dependency only AFTER disabled-by-default/CI guards.
const { chromium, expect } = await import('@playwright/test')
let browser
let stage = 'launch'
try {
  browser = await chromium.launch({headless:false})
  const ctx = await browser.newContext({
    acceptDownloads:false, serviceWorkers:'block',
    permissions:[], viewport:{width:1280,height:850},
  })
  const page = await ctx.newPage()
  // User enters credentials only inside actual app's HTTPS login page;
  // this script cannot read them and never records screenshots/videos/traces.
  stage = 'sign-in'
  await page.goto(HOST + '/account', {waitUntil:'domcontentloaded', timeout:30000})
  await expect(page.getByText('Signed in as', {exact:false})).toBeVisible({timeout:180000})
  stage = 'campaigns'
  await page.goto(HOST + '/campaigns', {waitUntil:'domcontentloaded', timeout:30000})
  const shop = page.locator('#rg-shop')
  await expect(shop).toBeVisible({timeout:30000})
  const match = await shop.locator('option').evaluateAll((options,id) =>
    options.some(option => option.value === id), expectedShop)
  if (!match) throw Error('Current signed-in account cannot access expected DEV shop')
  const rendered = await page.getByText(/verified render jobs completed/i).count()
  stage = 'trends'
  await page.goto(HOST + '/trends', {waitUntil:'domcontentloaded', timeout:30000})
  const checkbox = page.getByRole('checkbox', {name:'Improve Prompt with AI'})
  await expect(checkbox).toBeVisible({timeout:30000})
  const paidCheckbox = page.getByRole('checkbox', {
    name:'Use real Azure AI model (requires approved shop budget)',
  })
  await expect(paidCheckbox).not.toBeChecked()
  // This script never clicks prompt-generation, media upload, publishing or
  // anything with a cost or server mutation. Lack of live trend is reported
  // as an unmet hosted acceptance gate rather than a fabricated success.
  const legacyPrompt = await page.getByText(
    /Improvement never runs automatically/i).count()
  const automaticFreePrompt = await page.getByText(
    /When checked, a free enhanced prompt preview appears automatically/i).count()
  const results = {
    stage:'COMPLETE', signed_in:true, expected_shop_visible:true,
    campaigns_accessible:true, trends_accessible:true,
    prompt_checkbox_present:true, paid_ai_checked:false,
    new_free_prompt_ui_deployed:automaticFreePrompt > 0 && legacyPrompt === 0,
    legacy_prompt_ui_visible:legacyPrompt > 0,
    render_counter_visible:rendered > 0,
    actual_pexels_import_verified:false, actual_reel_render_verified:false,
    no_mutations_or_paid_calls_initiated_by_test:true,
  }
  console.log('RETAILGROWTH_DEV_READONLY_PLAYWRIGHT=' + JSON.stringify(results))
  await ctx.close()
} catch (error) {
  // NEVER log page content, screenshot, URLs with signed media tokens or
  // browser storage. Print a deliberately fixed stage diagnostic only.
  console.error('RETAILGROWTH_DEV_READONLY_PLAYWRIGHT_FAILED_STAGE=' + stage)
  process.exitCode = 1
} finally {
  if (browser) await browser.close()
}
