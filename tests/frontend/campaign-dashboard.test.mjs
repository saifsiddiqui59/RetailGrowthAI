import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import {
  buildCampaignRequest, cloneCampaign, formatDayDate, linkedInText,
  serializeDraftDay, timelineErrors, updateCampaignDay, updateScene,
} from '../../frontend/src/features/campaigns/campaign-model.mjs'

const fixture = JSON.parse(await readFile(
  new URL('../../frontend/src/features/campaigns/fixtures/sample-campaign.json', import.meta.url), 'utf8'
))
const day = fixture.days[0]
const validBrief = 'Create seven daily posts for the upcoming collection.'

test('maps a natural language brief to exactly the v1 authenticated API request fields', () => {
  const request = buildCampaignRequest({ brief: '  ' + validBrief + '  ', start_date: '2026-11-01' }, fixture)
  assert.deepEqual(Object.keys(request).sort(), [
    'brief', 'duration_days', 'language', 'media_asset_ids', 'offer',
    'platforms', 'shop_id', 'start_date', 'timezone',
  ])
  assert.equal(request.brief, validBrief)
  assert.equal(request.shop_id, fixture.shop_id)
  assert.equal(request.duration_days, 7)
  assert.deepEqual(request.platforms, ['linkedin', 'instagram'])
  assert.deepEqual(request.media_asset_ids, []) // fixture media IDs are NOT real authorized assets
  assert.equal(request.offer, null)
  assert.equal(request.timezone, 'Asia/Kolkata')
})

test('does not invent promotional offers and accepts explicit offer expiry', () => {
  const request = buildCampaignRequest({
    brief: validBrief, start_date: '2026-11-01',
    offer_description: '20% off approved items', offer_valid_until: '2026-11-07',
  }, fixture)
  assert.deepEqual(request.offer, { description: '20% off approved items', valid_until: '2026-11-07' })
})

test('rejects missing brief, impossible date, incomplete and expired offers', () => {
  assert.throws(() => buildCampaignRequest({ brief: 'short', start_date: '2026-11-01' }, fixture), /10/)
  assert.throws(() => buildCampaignRequest({ brief: validBrief, start_date: '2026-02-30' }, fixture), /start date/)
  assert.throws(() => buildCampaignRequest({
    brief: validBrief, start_date: '2026-11-01', offer_description: '20% off',
  }, fixture), /expiry/)
  assert.throws(() => buildCampaignRequest({
    brief: validBrief, start_date: '2026-11-01', offer_valid_until: '2026-11-07',
  }, fixture), /description/)
  assert.throws(() => buildCampaignRequest({
    brief: validBrief, start_date: '2026-11-01', offer_description: '20% off', offer_valid_until: '2026-10-31',
  }, fixture), /before/)
})

test('fixture storyboard is valid and has three 10-second scenes', () => {
  assert.deepEqual(timelineErrors(day.instagram.reel.storyboard), [])
  assert.deepEqual(day.instagram.reel.storyboard.map(scene => scene.start_seconds), [0, 10, 20])
})

test('editing scene duration recalculates starts and flags non-30-second timeline', () => {
  const original = cloneCampaign(fixture)
  const edited = updateScene(day.instagram.reel.storyboard, 0, 'duration_seconds', '12')
  assert.deepEqual(edited.map(scene => scene.start_seconds), [0, 12, 22])
  assert.ok(timelineErrors(edited).some(error => error.includes('32s')))
  assert.deepEqual(original, fixture)
  assert.deepEqual(fixture.days[0].instagram.reel.storyboard.map(scene => scene.start_seconds), [0, 10, 20])
  const fixed = updateScene(edited, 1, 'duration_seconds', '8')
  assert.deepEqual(timelineErrors(fixed), [])
})

test('empty scene copy, invalid UUID and zero duration cannot export', () => {
  const empty = updateScene(day.instagram.reel.storyboard, 2, 'overlay_text', ' ')
  assert.ok(timelineErrors(empty).some(error => error.includes('overlay text')))
  assert.throws(() => serializeDraftDay({
    ...day, instagram: { ...day.instagram, reel: { ...day.instagram.reel, storyboard: empty } },
  }), /Fix the storyboard/)
  assert.ok(timelineErrors(updateScene(day.instagram.reel.storyboard, 1, 'duration_seconds', 0)).length > 0)
  assert.ok(timelineErrors([{ ...day.instagram.reel.storyboard[0], asset_id: '../../private/file.png' }]).length > 0)
})

test('only requested campaign day changes and missing day is rejected', () => {
  const changed = updateCampaignDay(fixture, day.id, current => ({
    ...current, linkedin: { ...current.linkedin, post_text: 'Revised draft' },
  }))
  assert.equal(changed.days[0].linkedin.post_text, 'Revised draft')
  assert.deepEqual(changed.days.slice(1), fixture.days.slice(1))
  assert.notEqual(changed, fixture)
  assert.notEqual(changed.days[0], fixture.days[0])
  assert.throws(() => updateCampaignDay(fixture, 'unknown', current => current), /Unknown/)
})

test('local day export retains the contract fields and never produces a fake MP4', () => {
  const draft = JSON.parse(serializeDraftDay(day))
  assert.equal(draft.id, day.id)
  assert.equal(draft.instagram.reel.duration_seconds, 30)
  assert.equal(draft.instagram.reel.aspect_ratio, '9:16')
  assert.equal(draft.review_status, 'DRAFT')
  assert.ok(linkedInText(day).includes(day.linkedin.hashtags.join(' ')))
  assert.match(formatDayDate('2026-11-01'), /Nov/)
})

test('rejects invalid edit operation', () => {
  assert.throws(() => updateScene(day.instagram.reel.storyboard, 0, 'asset_id', 'arbitrary'), /Unsupported/)
  assert.throws(() => updateScene(day.instagram.reel.storyboard, 99, 'overlay_text', 'a'), /does not exist/)
})
