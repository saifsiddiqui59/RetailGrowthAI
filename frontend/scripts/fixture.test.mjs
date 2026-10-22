import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'

const file = new URL('../src/features/campaigns/fixtures/sample-campaign.json', import.meta.url)
const campaign = JSON.parse(await readFile(file, 'utf8'))
const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i
const datePattern = /^\d{4}-\d{2}-\d{2}$/

test('campaign fixture follows the v1 normalized response shape', () => {
  assert.deepEqual(Object.keys(campaign).sort(), ['days', 'id', 'shop_id', 'status'])
  assert.match(campaign.id, uuid)
  assert.match(campaign.shop_id, uuid)
  assert.equal(typeof campaign.status, 'string')
  assert.equal(campaign.days.length, 7)
})

test('days are consecutive, tenant-bound and channel-complete', () => {
  const ids = new Set()
  const topics = new Set()
  const firstDate = Date.parse(campaign.days[0].scheduled_date + 'T00:00:00Z')
  assert.ok(Number.isFinite(firstDate))
  for (const [index, day] of campaign.days.entries()) {
    assert.deepEqual(Object.keys(day).sort(), [
      'campaign_id', 'day_index', 'id', 'instagram', 'linkedin',
      'review_status', 'scheduled_date', 'shop_id', 'topic'
    ])
    assert.match(day.id, uuid)
    ids.add(day.id)
    assert.equal(day.campaign_id, campaign.id)
    assert.equal(day.shop_id, campaign.shop_id)
    assert.equal(day.day_index, index + 1)
    assert.match(day.scheduled_date, datePattern)
    assert.equal(Date.parse(day.scheduled_date + 'T00:00:00Z'), firstDate + index * 86_400_000)
    assert.ok(day.topic.trim())
    topics.add(day.topic)
    assert.ok(day.linkedin.post_text.trim())
    assert.ok(Array.isArray(day.linkedin.hashtags) && day.linkedin.hashtags.length > 0)
    assert.ok(day.linkedin.hashtags.every(tag => typeof tag === 'string' && tag.startsWith('#')))
    assert.ok(day.instagram.caption.trim())
    assert.equal(day.instagram.banner_asset_id, null)
    assert.equal(day.review_status, 'DRAFT')
    const reel = day.instagram.reel
    assert.equal(reel.duration_seconds, 30)
    assert.equal(reel.aspect_ratio, '9:16')
    assert.equal(reel.music_asset_id, null)
    assert.ok(reel.cta.trim())
    assert.ok(reel.storyboard.length > 0)
    let nextStart = 0
    for (const segment of reel.storyboard) {
      assert.deepEqual(Object.keys(segment).sort(), [
        'asset_id', 'duration_seconds', 'overlay_text', 'start_seconds'
      ])
      assert.equal(segment.start_seconds, nextStart)
      assert.ok(segment.duration_seconds > 0)
      assert.match(segment.asset_id, uuid)
      assert.ok(segment.overlay_text.trim())
      nextStart += segment.duration_seconds
    }
    assert.equal(nextStart, 30)
  }
  assert.equal(ids.size, 7)
  assert.equal(topics.size, 7)
})


test('static preview provides SPA fallback without rewriting built assets', async () => {
  const config = JSON.parse(await readFile(new URL('../public/staticwebapp.config.json', import.meta.url), 'utf8'))
  assert.equal(config.navigationFallback.rewrite, '/index.html')
  assert.ok(config.navigationFallback.exclude.includes('/assets/*'),
    'Vite assets must not be rewritten to index.html')
  assert.ok(config.navigationFallback.exclude.some(rule => rule.includes('json') && rule.includes('js')),
    'Missing assets should remain 404, not be rewritten as HTML')
  assert.equal(config.globalHeaders['X-Content-Type-Options'], 'nosniff')
})

test('SPA shell retains overview, campaigns, account and explicit mock mode', async () => {
  const app = await readFile(new URL('../src/App.jsx', import.meta.url), 'utf8')
  const campaignSource = await readFile(new URL('../src/features/campaigns/CampaignDashboard.jsx', import.meta.url), 'utf8')
  const auth = await readFile(new URL('../src/lib/supabase.js', import.meta.url), 'utf8')
  for (const route of ['/', '/campaigns', '/account']) {
    assert.ok(app.includes('path="' + route + '"'), 'Missing React route: ' + route)
  }
  assert.match(campaignSource, /Demo only · Sample drafts/)
  assert.match(campaignSource, /Preview campaign request/)
  assert.match(auth, /if \(!sharedClient\) sharedClient = createRetailClient\(\)/)
  assert.equal(campaign.days.length, 7)
})
