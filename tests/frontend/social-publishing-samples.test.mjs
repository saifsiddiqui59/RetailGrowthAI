import test from 'node:test'
import assert from 'node:assert/strict'
import { SOCIAL_PUBLISHING_SAMPLES as samples } from '../../frontend/src/features/social/social-publishing-samples.mjs'

test('each of the four agreed publishing providers has an independent offline sample', () => {
  assert.equal(samples.length, 4)
  assert.deepEqual(new Set(samples.map(sample => sample.provider)),
    new Set(['linkedin', 'facebook', 'instagram', 'youtube']))
  for (const sample of samples) {
    assert.match(sample.id, /^[a-z]+-[a-z]+$/)
    assert.ok(sample.title.length > 8)
    assert.ok(sample.copy.length > 40)
    assert.ok(Array.isArray(sample.required) && sample.required.length >= 3)
    assert.ok(sample.required.every(step => step.length > 12))
    assert.match(sample.schedule, /Draft only/)
    assert.ok(!('token' in sample) && !('credential' in sample))
    assert.ok(!('account_id' in sample) && !('shop_id' in sample))
    assert.ok(!('asset_id' in sample) && !('remote_post_id' in sample))
    assert.doesNotMatch(JSON.stringify(sample), /Bearer |client_secret|access_token|https:\/\//i)
  }
})

test('text publishing samples never require fake media', () => {
  for (const provider of ['linkedin', 'facebook']) {
    const sample = samples.find(item => item.provider === provider)
    assert.equal(sample.mediaKind, 'text')
    assert.equal(sample.media, undefined)
  }
})

test('Reels and Shorts only reference media to be supplied by approved Part 1', () => {
  for (const provider of ['instagram', 'youtube']) {
    const sample = samples.find(item => item.provider === provider)
    assert.equal(sample.mediaKind, 'video')
    assert.deepEqual(sample.media, {
      kind: 'video',
      aspectRatio: '9:16',
      durationSeconds: 30,
      source: 'Approved Part 1 private render (not provided in this sample)',
    })
    assert.match(sample.warning, /placeholder|Sample defaults/)
  }
})
