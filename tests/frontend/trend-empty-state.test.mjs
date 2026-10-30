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

test('existing DEV Free SWA release remains one-shot, protected and resource-scoped', () => {
  const workflow = readFileSync(new URL('../../.github/workflows/retail-dev-feature2-evergreen-fallback-swa-once.yml', import.meta.url), 'utf8')
  assert.match(workflow, /branches: \[main\]/)
  assert.match(workflow, /environment: dev/)
  assert.match(workflow, /release\(dev\): publish Feature2 honest no-trend Free SWA/)
  assert.match(workflow, /retailgrowthai-dev-preview/)
  assert.match(workflow, /static-web-apps-deploy/)
  assert.match(workflow, /FEATURE2_FREE_SWA_NO_TREND_FALLBACK=PASS/)
  assert.match(workflow, /if \[ -f package-lock\.json \]; then npm ci --no-audit --no-fund; else npm install --no-audit --no-fund; fi/)
  for (const forbidden of ['workflow_dispatch:', 'az group create', 'az staticwebapp create',
    'az functionapp create', 'az containerapp', 'az vm create', 'supabase db push']) {
    assert.equal(workflow.includes(forbidden), false)
  }
})
