import test from 'node:test'
import assert from 'node:assert/strict'
import { createCampaignApi, validateSignedVideoUrl } from '../../frontend/src/features/campaigns/campaign-api.mjs'

const ID = 'b1000000-0000-4000-8000-000000000001'

test('API mode stays off without configured origin', () => {
  assert.equal(createCampaignApi({ baseUrl: '', tokenProvider: async () => 'token' }), null)
  assert.throws(() => createCampaignApi({
    baseUrl: 'http://insecure.test', tokenProvider: async () => 'token'
  }), /HTTPS/)
})

test('campaign job uses verified bearer and expected contract URL', async () => {
  const requests = []
  const api = createCampaignApi({
    baseUrl: 'https://retail-api.example.com',
    tokenProvider: async () => 'refreshed-signed-jwt',
    fetchImpl: async (url, options) => {
      requests.push({ url, options })
      return { ok: true, json: async () => ({ campaign_id: ID, status: 'PLANNING' }) }
    },
  })
  assert.equal((await api.createCampaign({ brief: 'Test' })).status, 'PLANNING')
  assert.equal(requests[0].url, 'https://retail-api.example.com/api/campaigns')
  assert.equal(requests[0].options.headers.Authorization, 'Bearer refreshed-signed-jwt')
  assert.equal(requests[0].options.redirect, 'error')
})

test('cross-tenant and auth errors do not masquerade as success', async () => {
  const api = createCampaignApi({
    baseUrl: 'https://retail-api.example.com',
    tokenProvider: async () => 'token',
    fetchImpl: async () => ({ ok: false, status: 403, json: async () => ({ error: 'FORBIDDEN' }) }),
  })
  await assert.rejects(() => api.getCampaign(ID), error => error.status === 403)
  assert.throws(() => api.getCampaign('../../escape'), /resource ID/)
})

test('render job and download routes validate IDs', async () => {
  const paths = []
  const api = createCampaignApi({
    baseUrl: 'https://retail-api.example.com',
    tokenProvider: async () => 'token',
    fetchImpl: async (url) => { paths.push(url); return {
      ok: true, json: async () => ({ job_id: ID, status: 'QUEUED' }),
    } },
  })
  await api.createRender(ID, ID)
  await api.getRenderJob(ID)
  await api.getDownload(ID)
  assert.deepEqual(paths, [
    'https://retail-api.example.com/api/campaigns/' + ID + '/renders',
    'https://retail-api.example.com/api/render-jobs/' + ID,
    'https://retail-api.example.com/api/render-jobs/' + ID + '/download',
  ])
})

test('downloads may only open verified Supabase private storage', () => {
  const good = 'https://my-shop.supabase.co/storage/v1/object/sign/retailgrowth-media/' + ID + '/reel.mp4?token=signed'
  assert.equal(validateSignedVideoUrl(good, 'https://my-shop.supabase.co'), good)
  assert.throws(() => validateSignedVideoUrl(
    'https://evil.example.com/storage/v1/object/sign/retailgrowth-media/x?token=signed',
    'https://my-shop.supabase.co'), /private storage/)
  assert.throws(() => validateSignedVideoUrl(
    'https://my-shop.supabase.co/storage/v1/object/public/retailgrowth-media/x',
    'https://my-shop.supabase.co'), /private storage/)
})
