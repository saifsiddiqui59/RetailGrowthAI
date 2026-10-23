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


test('live draft save sends only editable fields with refreshed user JWT', async () => {
  const seen = []
  const api = createCampaignApi({
    baseUrl: 'https://retail-api.example.com',
    tokenProvider: async () => 'live-user-jwt',
    fetchImpl: async (url, options) => {
      seen.push({ url, options })
      return { ok: true, json: async () => ({ day: { id: ID } }) }
    },
  })
  const draft = {
    id: 'forged-identity', shop_id: 'forged-shop', review_status: 'APPROVED',
    topic: 'Fresh topic',
    linkedin: { post_text: 'New post', hashtags: ['#new'] },
    instagram: { caption: 'New caption' },
  }
  const saved = await api.saveDay(ID, ID, draft)
  assert.equal(saved.day.id, ID)
  assert.equal(seen[0].url, 'https://retail-api.example.com/api/campaigns/' + ID + '/days/' + ID)
  assert.equal(seen[0].options.method, 'PATCH')
  assert.equal(seen[0].options.headers.Authorization, 'Bearer live-user-jwt')
  assert.deepEqual(JSON.parse(seen[0].options.body), {
    topic: draft.topic, linkedin: draft.linkedin, instagram: draft.instagram,
  })
  assert.throws(() => api.saveDay('../unknown', ID, draft), /resource ID/)
})

test('remote edit conflict returns a 409 rather than silently overwriting', async () => {
  const api = createCampaignApi({
    baseUrl: 'https://retail-api.example.com',
    tokenProvider: async () => 'signed',
    fetchImpl: async () => ({
      ok: false, status: 409,
      json: async () => ({ error: 'EDIT_CONFLICT' }),
    }),
  })
  await assert.rejects(() => api.saveDay(ID, ID, {
    topic: 'Test', linkedin: {}, instagram: {},
  }), error => error.status === 409)
})

test('expired API token never returns a successful draft and a missing session blocks requests', async () => {
  let calls = 0
  const expired = createCampaignApi({
    baseUrl: 'https://retail-api.example.com',
    tokenProvider: async () => 'expired',
    fetchImpl: async (_, options) => {
      calls++
      assert.equal(options.cache, 'no-store')
      return { ok: false, status: 401, json: async () => ({ error: 'UNAUTHORIZED' }) }
    },
  })
  await assert.rejects(() => expired.getCampaign(ID), error =>
    error.status === 401 && /sign in again/.test(error.message))
  assert.equal(calls, 1)
  const unauthenticated = createCampaignApi({
    baseUrl: 'https://retail-api.example.com',
    tokenProvider: async () => '',
    fetchImpl: async () => { throw new Error('Should never fetch without JWT') },
  })
  await assert.rejects(() => unauthenticated.getCampaign(ID), /sign in again/)
})

test('frontend rejects origin credentials, query keys and non-HTTPS signed URLs', () => {
  for (const baseUrl of ['https://user:pass@api.example', 'https://api.example?token=x',
    'https://api.example/api', 'https://api.example/#fragment']) {
    assert.throws(() => createCampaignApi({ baseUrl, tokenProvider: async () => 'jwt' }), /HTTPS origin/)
  }
  assert.throws(() => validateSignedVideoUrl(
    'http://my-shop.supabase.co/storage/v1/object/sign/retailgrowth-media/x?token=abc',
    'https://my-shop.supabase.co'), /private storage/)
})
