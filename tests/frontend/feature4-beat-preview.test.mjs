// Display-only beat markers are bounded, millisecond-precise and tenant-scoped.
import assert from 'node:assert/strict'
import test from 'node:test'
import {proposedBeatMarkers} from '../../frontend/src/features/video/beat-preview.mjs'
const SHOP='11111111-1111-4111-8111-111111111111'
const plan={shop_id:SHOP,mode:'music_sync',duration_seconds:30,
            music_asset_id:'music01',beats:[1,2.125,5.01,10.01,15.01]}
const music=[{id:'music01',shop_id:SHOP,kind:'audio',authorized:true}]
test('valid same-shop measured beat proposals retain source millisecond precision',()=>{
  assert.deepEqual(proposedBeatMarkers(plan,music),plan.beats)
})
test('forged, foreign, unlicensed or out of range beat proposals are hidden',()=>{
  for(const wrong of [
    [], [{...music[0],shop_id:'foreign'}],
    [{...music[0],authorized:false}], [{...music[0],kind:'image'}],
  ]) assert.deepEqual(proposedBeatMarkers(plan,wrong),[])
  for(const beats of [[5,5],[5,4],[5,31],[NaN,5],[1.0001,5],[]])
    assert.deepEqual(proposedBeatMarkers({...plan,beats},music),[])
  assert.deepEqual(proposedBeatMarkers({...plan,mode:'media'},music),[])
})
test('a 60-second track never renders more than 120 preview markers',()=>{
  const beats=Array.from({length:240},(_,i)=>i*.25)
  const markers=proposedBeatMarkers({...plan,duration_seconds:60,beats},music)
  assert.equal(markers.length,120)
  assert.equal(markers[0],0)
  assert.equal(markers[1],.5)
})
