import test from 'node:test'
import assert from 'node:assert/strict'
import {
  compatibleMedia, makeVideoDraft, shiftVideoScene, retimeVideoDraft, recalculateScenes, validateVideoDraft,
} from '../../frontend/src/features/video/video-model.mjs'

const shopId = '11111111-1111-4111-8111-111111111111'
const media = [
  { id: 'good_photo', kind: 'image', authorized: true, shop_id: shopId },
  { id: 'good_video', kind: 'video', authorized: true, shop_id: shopId },
  { id: 'poster1', kind: 'poster', authorized: true, shop_id: shopId },
  { id: 'denied_photo', kind: 'image', authorized: false, shop_id: shopId },
]
const tracks = [{ id: 'licensed1', title: 'Owned track', authorized: true, kind: 'audio', shop_id: shopId }]

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
  assert.match(validateVideoDraft(plan, media).join(' '), /authorized same-shop media/)
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

test('duration changes preserve the drafted professional story and authorized media', () => {
  const draft = makeVideoDraft({ shopId, mode: 'media', duration: 30, mediaAssets: media })
  draft.scenes[1].headline = 'Our actual approved kurti'
  draft.scenes[1].offer = '20% OFF'
  const longer = retimeVideoDraft(draft, 60)
  assert.deepEqual(longer.scenes.map(s => s.start), [0, 20, 40])
  assert.deepEqual(longer.scenes.map(s => s.duration), [20, 20, 20])
  assert.equal(longer.scenes[1].headline, 'Our actual approved kurti')
  assert.equal(longer.scenes[1].offer, '20% OFF')
  assert.equal(longer.scenes[1].asset_id, draft.scenes[1].asset_id)
  assert.deepEqual(validateVideoDraft(longer, media, tracks), [])
  const shorter = retimeVideoDraft(longer, 15)
  assert.deepEqual(shorter.scenes.map(s => s.start), [0, 5, 10])
  assert.deepEqual(validateVideoDraft(shorter, media, tracks), [])
  assert.equal(draft.duration_seconds, 30)
})

test('retiming never silently drops a short scene', () => {
  const draft = makeVideoDraft({ shopId, mode: 'text', duration: 60 })
  draft.scenes = Array.from({ length: 12 }, (_, i) => ({
    start: i === 0 ? 0 : i < 11 ? i - 1 : 10,
    duration: i < 11 ? .5 : 54.5,
    headline: 'Approved',
  }))
  assert.throws(() => retimeVideoDraft(draft, 15), /shorter than half a second/)
})

test('scene motion and separate poster overlays are allowlisted, never custom expressions', () => {
  const draft = makeVideoDraft({ shopId, mode: 'media', mediaAssets: media })
  draft.scenes[1].animation_preset = 'pop'
  draft.scenes[1].transition = 'slide'
  draft.scenes[1].poster_overlay_asset_id = 'poster1'
  assert.deepEqual(validateVideoDraft(draft, media, tracks), [])
  draft.scenes[1].transition = 'url(javascript:alert(1))'
  assert.match(validateVideoDraft(draft, media, tracks).join(' '), /unapproved transition/)
  draft.scenes[1].transition = 'cut'
  draft.scenes[1].poster_overlay_asset_id = 'denied_photo'
  assert.match(validateVideoDraft(draft, media, tracks).join(' '), /authorized promotional poster/)
  draft.scenes[1].poster_overlay_asset_id = draft.scenes[1].asset_id
  assert.match(validateVideoDraft(draft, media, tracks).join(' '), /distinct authorized/)
})
