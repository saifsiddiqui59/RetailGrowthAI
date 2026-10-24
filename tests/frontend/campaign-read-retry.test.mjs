import test from 'node:test'
import assert from 'node:assert/strict'
import { createCampaignApi } from '../../frontend/src/features/campaigns/campaign-api.mjs'

const ID = '11111111-1111-4111-8111-111111111111'
const ENDPOINT = 'https://retail-api.example.com'

function makeApi(fetchImpl, tokenProvider = async () => 'signed-retailer-jwt') {
  return createCampaignApi({ baseUrl: ENDPOINT, tokenProvider, fetchImpl })
}
const http = (status, error = null) => ({
  status, ok: status >= 200 && status < 300,
  json: async () => error === null ? { id: ID, status: 'DRAFT' } : { error },
})

test('GET attempts one bounded identical retry after prehandler 503 only', async () => {
  let calls = 0
  const seen = []
  const api = makeApi(async (url, options) => {
    seen.push({ url, options })
    calls++
    return calls === 1 ? http(503, 'SERVICE_UNAVAILABLE') : http(200)
  })
  const response = await api.getCampaign(ID)
  assert.equal(response.id, ID)
  assert.equal(calls, 2)
  assert.equal(seen[0].url, seen[1].url)
  for (const { options } of seen) {
    assert.equal(options.method, 'GET')
    assert.equal(options.headers.Authorization, 'Bearer signed-retailer-jwt')
    assert.equal(options.cache, 'no-store')
    assert.equal(options.redirect, 'error')
    assert.ok(options.signal instanceof AbortSignal)
    assert.equal(options.body, undefined)
  }
})

test('GET never retries a denied tenant, expired login or absent resource', async () => {
  for (const [status,code] of [[401,'UNAUTHORIZED'],[403,'FORBIDDEN'],[404,'NOT_FOUND'],
                                [402,'SUBSCRIPTION_REQUIRED'],[429,'QUOTA_EXCEEDED']]) {
    let calls = 0
    const api = makeApi(async () => { calls++; return http(status,code) })
    await assert.rejects(() => api.getCampaign(ID), error => error.status === status)
    assert.equal(calls, 1)
  }
})

test('GET network error has at most two attempts, then a bounded 503', async () => {
  let calls = 0
  const api = makeApi(async () => { calls++; throw new TypeError('network offline') })
  await assert.rejects(() => api.getPosterJob(ID),
    err => err.status === 503 && /temporarily unavailable/.test(err.message))
  assert.equal(calls, 2)
})

test('AbortError is retryable only for GET and does not leak raw exception message', async () => {
  let calls = 0
  const error = new Error('sensitive-network-context')
  error.name = 'AbortError'
  const api = makeApi(async () => { calls++; throw error })
  await assert.rejects(() => api.getDownload(ID), e => {
    assert.equal(e.status, 503)
    assert.doesNotMatch(e.message,/sensitive-network-context/)
    return true
  })
  assert.equal(calls, 2)
})

test('POST/PATCH never replay ambiguous server 5xx or network loss', async () => {
  let calls = 0
  const api = makeApi(async (_, opts) => {
    calls++
    assert.equal(opts.signal, undefined)
    return http(503, 'SERVICE_UNAVAILABLE')
  })
  await assert.rejects(() => api.createCampaign({ brief:'no-publish' }), e => e.status === 503)
  await assert.rejects(() => api.createRender(ID,ID), e => e.status === 503)
  await assert.rejects(() => api.saveDay(ID,ID,{topic:'t',linkedin:{},instagram:{}}),e => e.status===503)
  await assert.rejects(() => api.selectPosterBanner(ID,{banner_asset_id:null}),e => e.status===503)
  assert.equal(calls,4)
})

test('even a transient 503 on GET stops after the second response', async () => {
  let calls = 0
  const api = makeApi(async () => { calls++; return http(503, 'SERVICE_UNAVAILABLE') })
  await assert.rejects(() => api.listPosterDrafts(ID,ID), e => e.status === 503)
  assert.equal(calls,2)
})

test('no missing session is turned into a retry', async () => {
  let calls=0
  const api=makeApi(async()=>{ calls++; return http(200) },async()=>'')
  await assert.rejects(() => api.getRenderJob(ID), /sign in again/)
  assert.equal(calls,0)
})
