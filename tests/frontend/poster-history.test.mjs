import test from 'node:test'
import assert from 'node:assert/strict'
import { createCampaignApi } from '../../frontend/src/features/campaigns/campaign-api.mjs'

const CID = '11111111-1111-4111-8111-111111111111'
const DID = '22222222-2222-4222-8222-222222222222'
const PID = '33333333-3333-4333-8333-333333333333'

test('poster history uses signed-in JWT and exact saved campaign/day path', async () => {
  const calls = []
  const api = createCampaignApi({
    baseUrl: 'https://api.example.test',
    tokenProvider: async () => 'signed-in-user-JWT',
    fetchImpl: async (url, request) => {
      calls.push({url, request})
      return {ok:true,status:200,json:async()=>({posters:[{poster_id:PID,status:'READY'}]})}
    },
  })
  assert.equal((await api.listPosterDrafts(CID,DID)).posters[0].poster_id,PID)
  assert.equal(calls.length,1)
  assert.equal(calls[0].url,
    'https://api.example.test/api/campaigns/' + CID + '/days/' + DID + '/posters')
  assert.equal(calls[0].request.method,'GET')
  assert.equal(calls[0].request.headers.Authorization,'Bearer signed-in-user-JWT')
  assert.equal(calls[0].request.body,undefined)
  assert.equal(calls[0].request.cache,'no-store')
})

test('invalid IDs, denied JWT and forbidden origin fail before showing history', async () => {
  let network = 0
  const api = createCampaignApi({
    baseUrl:'https://api.example.test',
    tokenProvider:async()=> '',
    fetchImpl:async()=>{network++;return {ok:true,status:200,json:async()=>({})}},
  })
  await assert.rejects(()=>api.listPosterDrafts('invalid',DID),/Invalid resource ID/)
  await assert.rejects(()=>api.listPosterDrafts(CID,DID),/sign in/i)
  assert.equal(network,0)
  assert.throws(()=>createCampaignApi({
    baseUrl:'http://insecure.example',tokenProvider:async()=> 'JWT'}),/HTTPS/)
})
