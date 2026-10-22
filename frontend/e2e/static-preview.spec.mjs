import { test, expect } from '@playwright/test'

// These checks run only against Vite's local test server. They do not need Azure
// Static Web Apps, Supabase, a deployed API or production credentials.
test('direct / navigation displays the existing overview', async ({ page }) => {
  await page.goto('/')
  await expect(page).toHaveURL(/\/$/)
  await expect(page.getByRole('heading', { name: 'Campaign workspace' })).toBeVisible()
  await expect(page.getByText('Mock campaign days')).toBeVisible()
  await expect(page.getByRole('navigation', { name: 'Main navigation' }).getByRole('link', { name: 'Campaigns' })).toBeVisible()
})

test('direct /campaigns loads the editable seven-day demo without calling external services', async ({ page }) => {
  const externalRequests = []
  page.on('request', request => {
    if (new URL(request.url()).origin !== 'http://127.0.0.1:5173') {
      externalRequests.push(request.url())
    }
  })
  await page.goto('/campaigns')
  await expect(page).toHaveURL(/\/campaigns$/)
  await expect(page.getByRole('heading', { name: /Make every day/ })).toBeVisible()
  await expect(page.getByText('Demo only · Sample drafts', { exact: false })).toBeVisible()
  await expect(page.getByRole('button', { name: /Preview campaign request/ })).toBeVisible()
  await page.getByRole('button', { name: /Preview campaign request/ }).click()
  await expect(page.getByText('No campaign was generated; the seven sample days below are unchanged.')).toBeVisible()
  expect(externalRequests).toEqual([])
})

test('direct /account loads existing account route and navigation remains client side', async ({ page }) => {
  await page.goto('/account')
  await expect(page).toHaveURL(/\/account$/)
  await expect(page.getByRole('heading', { name: 'Business account' })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Sign in' })).toBeVisible()
  await page.getByRole('navigation', { name: 'Main navigation' }).getByRole('link', { name: 'Campaigns' }).click()
  await expect(page).toHaveURL(/\/campaigns$/)
  await expect(page.getByRole('heading', { name: /Make every day/ })).toBeVisible()
})
