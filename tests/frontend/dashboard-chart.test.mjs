import { test } from 'node:test'
import assert from 'node:assert/strict'
import { verifiedCounts } from '../../frontend/src/features/dashboard/chart-model.mjs'

test('Chart.js receives only verified nonnegative server counts', () => {
  assert.equal(verifiedCounts([1, null], ['a', 'b']), null)
  assert.equal(verifiedCounts([0, -1], ['a', 'b']), null)
  assert.equal(verifiedCounts([3.1, 1], ['a', 'b']), null)
  assert.equal(verifiedCounts([4], ['a', 'b']), null)
  assert.equal(verifiedCounts([NaN], ['a']), null)
  assert.equal(verifiedCounts([], []), null)
  assert.deepEqual(verifiedCounts([0, 3], ['Campaigns', 'Reels']).datasets[0].data, [0, 3])
  assert.equal(verifiedCounts([0, 3], ['Campaigns', 'Reels']).labels[0], 'Campaigns')
})
