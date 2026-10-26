import test from 'node:test'
import assert from 'node:assert/strict'
import { createTrendApi } from '../../frontend/src/features/trends/trend-api.mjs'

const SHOP = '10000000-0000-4000-8000-000000000001'
const OTHER = '20000000-0000-4000-8000-000000000002'
const TREND = 'a'.repeat(32)

function api(fetchImpl, tokenProvider = async () => 'verified-shop-jwt') {
  return createTrendApi({ baseUrl: 'https://example.azurewebsites.net',
    tokenProvider, fetchImpl })
}

test('no trends API exists in demo mode, and invalid origins are never accepted', () => {
  assert.equal(createTrendApi({ baseUrl: '', tokenProvider: () => 'token' }), null)
  for (const origin of ['http://retail.example', 'https://evil.example/path',
    'https://user:pass@retail.example', 'https://retail.example?key=secret']) {
    assert.throws(() => createTrendApi({ baseUrl: origin, tokenProvider: () => 'token' }))
  }
})

test('signed GET uses authorized shop ID and never sends secret/personal data in URL', async () => {
  const calls = []
  const client = api(async (url, options) => {
    calls.push({ url, options })
    return { ok: true, status: 200, json: async () => ({ shop_id: SHOP, recommendations: [] }) }
  })
  assert.deepEqual(await client.getRecommendations(SHOP), { shop_id: SHOP, recommendations: [] })
  assert.equal(calls[0].url, 'https://example.azurewebsites.net/api/shops/' + SHOP + '/trend-recommendations')
  assert.equal(calls[0].options.headers.Authorization, 'Bearer verified-shop-jwt')
  assert.equal(calls[0].options.redirect, 'error')
  assert.equal(calls[0].options.cache, 'no-store')
  await assert.rejects(client.getRecommendations('not-uuid'))
  assert.equal(calls.length, 1)
})

test('draft creation validates tenant and trend before sending exactly one authenticated POST', async () => {
  const calls = []
  const client = api(async (url, options) => {
    calls.push({ url, options })
    return { ok: true, status: 201, json: async () => ({ draft_id: SHOP, shop_id: SHOP, status: 'DRAFT' }) }
  })
  const payload = { shop_id: SHOP, brief: 'Seven days of store styling',
    media_asset_ids: [OTHER] }
  assert.throws(() => client.createDraft(SHOP, 'not-signal', payload))
  assert.throws(() => client.createDraft(SHOP, TREND, { ...payload, shop_id: OTHER }))
  assert.equal(calls.length, 0)
  assert.equal((await client.createDraft(SHOP, TREND, payload)).status, 'DRAFT')
  assert.equal(calls.length, 1)
  assert.equal(calls[0].options.method, 'POST')
  assert.deepEqual(JSON.parse(calls[0].options.body), { trend_id: TREND, campaign: payload })
})

test('401 and unavailable source failures never fall back to anonymous reads or local guesses', async () => {
  let calls = 0
  const unauthorized = api(async () => {
    calls++
    return { ok: false, status: 401, json: async () => ({}) }
  })
  await assert.rejects(unauthorized.getRecommendations(SHOP), /session expired/i)
  const disabled = api(async () => {
    calls++
    return { ok: false, status: 503, json: async () => ({ error: 'FEATURE2_DISABLED' }) }
  })
  await assert.rejects(disabled.getRecommendations(SHOP), /unavailable in DEV/i)
  assert.equal(calls, 2)
  const noSession = api(async () => {
    throw new Error('no anonymous fallback allowed')
  }, async () => '')
  await assert.rejects(noSession.getRecommendations(SHOP), /sign in/i)
})
