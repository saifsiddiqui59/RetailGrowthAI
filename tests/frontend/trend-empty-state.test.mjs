import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { offerStandardCampaignFallback } from '../../frontend/src/features/trends/trend-empty-state.mjs'

test('no live matched trend -> existing ordinary campaign creator remains available', () => {
  assert.equal(offerStandardCampaignFallback({
    loading: false, error: '', results: { recommendations: [], sources: [], profile_required: false },
  }), true)
  assert.equal(offerStandardCampaignFallback({
    loading: false, error: 'Trends unavailable', results: null,
  }), true)
})
test('no fallback during loading, incomplete profile, or when relevant results exist', () => {
  assert.equal(offerStandardCampaignFallback({ loading: true, error: '', results: null }), false)
  assert.equal(offerStandardCampaignFallback({ loading: false, error: '', results: null }), false)
  assert.equal(offerStandardCampaignFallback({
    loading: false, error: '', results: { recommendations: [], profile_required: true },
  }), false)
  assert.equal(offerStandardCampaignFallback({
    loading: false, error: '', results: { recommendations: [{ trend_id: 'verified' }] },
  }), false)
})
test('fallback is navigation to existing campaign editor, not an unverified source POST', () => {
  const page = readFileSync(new URL('../../frontend/src/features/trends/TrendWorkspace.jsx', import.meta.url), 'utf8')
  assert.match(page, /offerStandardCampaignFallback\(\{ loading, error, results \}\)/)
  assert.match(page, /<Link to="\/campaigns">Create a standard campaign without a trend<\/Link>/)
  assert.match(page, /It will not claim that your topic is trending/)
  assert.doesNotMatch(page, /trend_id: ['"]evergreen['"]/)
})
