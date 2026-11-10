import test from 'node:test'
import assert from 'node:assert/strict'
import {localVoiceRequestScope,sameLocalVoiceScope} from
  '../../frontend/src/features/voiceover/local-voice-scope.mjs'

const cb = () => {}
const state = {
  shopId:'shop-a',campaignId:'campaign-a',planSha256:'a'.repeat(64),
  sourceScript:'Approved kurti story',enabled:true,
  voice:'af_heart',language:'en-us',speed:'normal',
  handlers:[cb,()=>{}],
}
const snapshot = overrides => localVoiceRequestScope({...state,...overrides})

test('unchanged tenant, voice and callback identities retain one in-flight response',()=>{
  assert.equal(sameLocalVoiceScope(snapshot(),snapshot()),true)
  assert.equal(sameLocalVoiceScope(null,snapshot()),false)
  assert.equal(sameLocalVoiceScope(snapshot(),null),false)
})

test('revocation, selection or reviewed source change invalidates stale local result',()=>{
  const previous=snapshot()
  for(const change of [
    {enabled:false},{shopId:'shop-b'},{campaignId:'campaign-b'},
    {planSha256:'b'.repeat(64)},{sourceScript:'Changed source script'},
    {voice:'af_sky'},{language:'en-gb'},{speed:'slow'},
    {handlers:[()=>{},state.handlers[1]]},
    {handlers:[cb]},{handlers:[cb,state.handlers[1],()=>{}]},
  ])assert.equal(sameLocalVoiceScope(previous,snapshot(change)),false)
})

test('scope snapshots are immutable and callback replacement is detected',()=>{
  const prior=snapshot()
  assert.equal(Object.isFrozen(prior),true)
  assert.equal(Object.isFrozen(prior.handlers),true)
  assert.equal(sameLocalVoiceScope(prior,snapshot()),true)
  assert.equal(sameLocalVoiceScope(prior,snapshot({
    handlers:[state.handlers[0],()=>{}],
  })),false)
})
