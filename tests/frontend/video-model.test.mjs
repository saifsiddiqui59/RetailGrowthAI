import test from 'node:test'
import assert from 'node:assert/strict'
import {
  compatibleMedia, makeVideoDraft, shiftVideoScene, recalculateScenes, validateVideoDraft,
} from '../../frontend/src/features/video/video-model.mjs'

const shopId = '11111111-1111-4111-8111-111111111111'
const media = [
  { id: 'good_photo', kind: 'image', authorized: true },
  { id: 'good_video', kind: 'video', authorized: true },
  { id: 'poster1', kind: 'poster', authorized: true },
  { id: 'denied_photo', kind: 'image', authorized: false },
]
const tracks = [{ id: 'licensed1', title: 'Owned track', authorized: true }]

test('P0 modes produce bounded v2 plans without granting media authority', () => {
  for (const mode of ['text', 'image', 'poster', 'media']) {
    const plan = makeVideoDraft({ shopId, mode, mediaAssets: media })
    assert.equal(plan.duration_seconds, 15)
    assert.equal(plan.scenes.reduce((sum, s) => sum + s.duration, 0), 15)
    assert.deepEqual(validateVideoDraft(plan, media, tracks), [])
  }
})

test('server authorization flags exclude revoked media', () => {
  assert.deepEqual(compatibleMedia('image', media).map(a => a.id), ['good_photo'])
  const plan = makeVideoDraft({ shopId, mode: 'image', mediaAssets: media })
  plan.scenes[1].asset_id = 'denied_photo'
  assert.match(validateVideoDraft(plan, media).join(' '), /authorized media/)
})

test('scene reordering recalculates non-overlapping time starts', () => {
  const plan = makeVideoDraft({ shopId, mode: 'text', duration: 30 })
  const reordered = shiftVideoScene(plan.scenes, 0, 1)
  assert.equal(reordered[0].headline, plan.scenes[1].headline)
  assert.equal(reordered[1].headline, plan.scenes[0].headline)
  assert.deepEqual(reordered.map(x => x.start), [0, 10, 20])
  assert.deepEqual(shiftVideoScene(reordered, 0, -1), reordered)
  assert.deepEqual(recalculateScenes(reordered), reordered)
})

test('cannot silently infer approved prices, beat data or music rights', () => {
  const plan = makeVideoDraft({ shopId, mode: 'music_sync', mediaAssets: media })
  assert.match(validateVideoDraft(plan, media, tracks).join(' '), /Beat-sync requires/)
  plan.music_asset_id = 'licensed1'
  plan.beats = [0, 5, 10]
  assert.deepEqual(validateVideoDraft(plan, media, tracks), [])
  plan.music_asset_id = 'untrusted'
  assert.match(validateVideoDraft(plan, media, tracks).join(' '), /rights-cleared/)
  plan.scenes[0].offer = 'x'.repeat(71)
  assert.match(validateVideoDraft(plan, media, tracks).join(' '), /Offer text/)
})

test('invalid lengths and unlicensed art reject submit', () => {
  const plan = makeVideoDraft({ shopId, mode: 'poster', mediaAssets: media })
  plan.scenes[0].duration = 7
  assert.match(validateVideoDraft(plan, media, tracks).join(' '), /sequential|fill/)
  plan.scenes[0].duration = 5
  plan.scenes[0].headline = ''
  assert.match(validateVideoDraft(plan, media, tracks).join(' '), /headline/)
})
