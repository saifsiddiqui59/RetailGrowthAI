import test from 'node:test'
import assert from 'node:assert/strict'
import { boundedFrameSeek } from '../../frontend/src/features/video/frame-seek.mjs'

test('F4-08 seek clamps to approved duration and whole frames', () => {
  assert.equal(boundedFrameSeek(-10, 30, 24), 0)
  assert.equal(boundedFrameSeek(99, 30, 24), 30)
  assert.equal(boundedFrameSeek(1 / 24, 30, 24), 1 / 24)
  assert.equal(boundedFrameSeek(0.08, 30, 30), 2 / 30)
  assert.equal(boundedFrameSeek(10.05, 10.05, 24), 10.041666666666666)
})
test('F4-08 rejects nonfinite and malformed seeks instead of poisoning playhead', () => {
  for (const value of [NaN, Infinity, -Infinity, undefined, null, '12', {}]) {
    assert.equal(boundedFrameSeek(value, 30, 24), null)
  }
  for (const duration of [0, -1, NaN, Infinity, '30']) {
    assert.equal(boundedFrameSeek(1, duration, 24), null)
  }
  assert.equal(boundedFrameSeek(1, 30, 0), null)
  assert.equal(boundedFrameSeek(1, 30, 60), null)
})
