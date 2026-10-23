import { test, expect } from '@playwright/test'

test('all four offline platform publishing samples can be inspected without OAuth or posting', async ({ page }) => {
  const externalPosts = []
  page.on('request', request => {
    if (/linkedin\.com|facebook\.com|instagram\.com|googleapis\.com|youtube\.com/.test(request.url())) {
      externalPosts.push(request.url())
    }
  })
  await page.goto('/social')
  const gallery = page.getByRole('region', { name: 'Four sample platform posts' })
  await expect(gallery).toBeVisible()
  await expect(gallery.getByRole('tab')).toHaveCount(4)
  await expect(gallery.getByText('No poster or video is generated here', {exact:false})).toBeVisible()
  await expect(gallery.getByText('DRAFT SAMPLE', {exact:false})).toBeVisible()
  for (const [platform, medium, phrase] of [
    ['LinkedIn', 'Text post', 'well-chosen shirt'],
    ['Facebook', 'Text post', 'What is your go-to shirt color?'],
    ['Instagram', 'Reel video', 'NO VIDEO ATTACHED'],
    ['YouTube', 'Short video', 'NO VIDEO ATTACHED'],
  ]) {
    const tab = gallery.getByRole('tab', {name: platform + ' ' + medium})
    await tab.click()
    await expect(tab).toHaveAttribute('aria-selected', 'true')
    await expect(gallery.getByRole('tabpanel')).toContainText(phrase)
    await expect(gallery.getByText('No poster or video is generated here', {exact:false})).toBeVisible()
  }
  expect(externalPosts).toEqual([])
})

test('the sample gallery stays usable in narrow mobile layout', async ({page}) => {
  await page.setViewportSize({width: 375, height: 780})
  await page.goto('/social')
  const gallery = page.getByRole('region', {name:'Four sample platform posts'})
  await gallery.getByRole('tab', {name:'Instagram Reel video'}).click()
  await expect(gallery.getByRole('img', {
    name:'Vertical video placeholder. No media generated or attached.',
  })).toBeVisible()
  await expect(gallery.getByText('Container creation, FINISHED processing', {exact:false})).toBeVisible()
})
