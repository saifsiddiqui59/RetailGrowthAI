import test from 'node:test'
import assert from 'node:assert/strict'
import { createCampaignApi, validateSignedVideoUrl } from '../../frontend/src/features/campaigns/campaign-api.mjs'

const CID = 'a1000000-0000-4000-8000-000000000001'
const PID = 'b1000000-0000-4000-8000-000000000002'
const JID = 'c1000000-0000-4000-8000-000000000003'
const DID = 'd1000000-0000-4000-8000-000000000004'
const AID = 'e1000000-0000-4000-8000-000000000005'

test('poster API uses only saved tenant UUIDs, bearer token and expected route', async () => {
  const requests = []
  const api = createCampaignApi({
    baseUrl: 'https://retail-api.example.com',
    tokenProvider: async () => 'current-user-jwt',
    fetchImpl: async (url, options) => {
      requests.push({ url, options })
      return { ok: true, status: 200, json: async () => ({ poster_id: PID, job_id: JID }) }
    },
  })
  await api.createPosterDraft(CID, {
    day_id: DID, source_asset_id: AID,
    template: 'editorial', format: 'square',
    business_name: 'Clothing Store', accent_color: '#AA6644',
    background_color: '#F5F0E8', offer_text: null,
  })
  await api.getPosterDraft(PID)
  await api.createPosterRender(PID)
  await api.getPosterJob(JID)
  await api.getPosterDownload(JID)
  await api.selectPosterBanner(PID, { caption: 'Review', banner_asset_id: null, reel: {} })
  assert.deepEqual(requests.map(x => [x.options.method, new URL(x.url).pathname]), [
    ['POST', '/api/campaigns/' + CID + '/posters'],
    ['GET', '/api/poster-drafts/' + PID],
    ['POST', '/api/poster-drafts/' + PID + '/renders'],
    ['GET', '/api/poster-jobs/' + JID],
    ['GET', '/api/poster-jobs/' + JID + '/download'],
    ['POST', '/api/poster-drafts/' + PID + '/select'],
  ])
  for (const { options } of requests) {
    assert.equal(options.headers.Authorization, 'Bearer current-user-jwt')
    assert.equal(options.cache, 'no-store')
    assert.equal(options.redirect, 'error')
  }
  assert.deepEqual(JSON.parse(requests[5].options.body), {
    expected_instagram: { caption: 'Review', banner_asset_id: null, reel: {} },
  })
})

test('invalid poster identities or local synthetic asset IDs are never transmitted', async () => {
  let count = 0
  const api = createCampaignApi({
    baseUrl: 'https://retail-api.example.com',
    tokenProvider: async () => 'jwt',
    fetchImpl: async () => { count++; return { ok: true, json: async () => ({}) } },
  })
  assert.throws(() => api.createPosterDraft('demo', { day_id: DID, source_asset_id: AID }), /resource ID/)
  assert.throws(() => api.selectPosterBanner('../poster', { banner_asset_id: null }), /resource ID/)
  assert.throws(() => api.selectPosterBanner(PID, {}), /complete saved/)
  assert.throws(() => api.getPosterDownload('not-a-uuid'), /resource ID/)
  assert.equal(count, 0)
})

test('poster downloads must originate from same private Supabase bucket', () => {
  const good = 'https://my-retail.supabase.co/storage/v1/object/sign/retailgrowth-media/' +
    CID + '/posters/' + PID + '/' + JID + '.png?token=short-lived'
  assert.equal(validateSignedVideoUrl(good, 'https://my-retail.supabase.co'), good)
  assert.throws(() => validateSignedVideoUrl(good.replace('my-retail', 'attacker'),
    'https://my-retail.supabase.co'), /private storage/)
  assert.throws(() => validateSignedVideoUrl(
    'https://my-retail.supabase.co/storage/v1/object/public/retailgrowth-media/x.png',
    'https://my-retail.supabase.co'), /private storage/)
})
