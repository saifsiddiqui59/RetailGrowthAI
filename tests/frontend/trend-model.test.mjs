import assert from 'node:assert/strict'
import { test } from 'node:test'
import { filterRecommendations, safeEvidence, sourceSummary } from '../../frontend/src/features/trends/trend-model.mjs'

const trend = {
  trend_id: '1'.repeat(32), category: 'clothing', language: 'mr-IN', city: 'Nagpur',
  score: 80, source: 'google_rss', evidence_url: 'https://trends.google.com/trending?geo=IN',
  observed_at: '2026-10-26T08:00:00+00:00', expires_at: '2026-10-27T08:00:00+00:00',
}
test('evidence urls are restricted to trusted https provider domains', () => {
  assert.ok(safeEvidence(trend.evidence_url, trend.source))
  assert.equal(safeEvidence('https://trends.google.com.evil.com/?x=1', 'google_rss'), null)
  assert.equal(safeEvidence('javascript:alert(1)', 'google_rss'), null)
  assert.equal(safeEvidence('https://example.com/', 'youtube'), null)
})
test('only active verified evidence and retailer filters show', () => {
  const now = new Date('2026-10-26T10:00:00Z')
  assert.equal(filterRecommendations([trend], {now}).length, 1)
  assert.equal(filterRecommendations([trend], {now, category:'restaurant'}).length, 0)
  assert.equal(filterRecommendations([trend], {now, city:'Mumbai'}).length, 0)
  assert.equal(filterRecommendations([trend], {now, language:'en-IN'}).length, 0)
  assert.equal(filterRecommendations([trend], {now:new Date('2026-10-28T10:00:00Z')}).length, 0)
})
test('source omissions are explicit, not represented as empty trend discovery', () => {
  assert.match(sourceSummary([]), /not configured/)
  assert.match(sourceSummary([{source:'youtube', status:'disabled'}]), /Incomplete sources/)
})
