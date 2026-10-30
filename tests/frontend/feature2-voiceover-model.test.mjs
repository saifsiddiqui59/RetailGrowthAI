import test from 'node:test'
import assert from 'node:assert/strict'
import {F2_VOICES,emptyVoiceSelection,makeVoiceAction,validateVoiceSelection,
  voiceChoices,isCurrentPrivateUpload} from '../../frontend/src/features/voiceover/voiceover-model.mjs'
const SHOP='11111111-1111-4111-8111-111111111111'
const CAM='22222222-2222-4222-8222-222222222222'
const ID='33333333-3333-4333-8333-333333333333'
const AID='44444444-4444-4444-8444-444444444444'
const SHA='a'.repeat(64)
const assets=[{id:AID,shop_id:SHOP,kind:'audio',authorized:true}]
const ai={mode:'ai',language:'en-IN',voice_id:'en-IN-NeerjaNeural',speed:'normal',audio_asset_id:null}
test('source-safe catalog English/Hindi/Marathi six actual standard neural choices',()=>{
 assert.equal(F2_VOICES.length,6)
 assert.equal(voiceChoices('hi-IN').length,2)
 assert.equal(voiceChoices('mr-IN').length,2)
 assert.deepEqual(new Set(F2_VOICES.map(x=>x.gender)),new Set(['Male','Female']))
})
test('AI choice validates and creates only explicit billed request',()=>{
 const out=makeVoiceAction({selection:ai,shopId:SHOP,campaignId:CAM,planSha256:SHA,
   userConfirmedCharge:true,idempotencyKey:ID,preview:true})
 assert.deepEqual(Object.keys(out).sort(),[
  'campaign_id','creative_plan_sha256','idempotency_key','language','preview',
  'shop_id','speed','user_confirmed_charge','voice_id'])
 assert.equal(out.preview,true)
 assert.equal(out.user_confirmed_charge,true)
})
test('no voice and uploaded audio modes require exact tenant-scoped approved media',()=>{
 assert.equal(validateVoiceSelection(emptyVoiceSelection(),{shopId:SHOP}).mode,'none')
 const uploaded={mode:'uploaded',language:null,voice_id:null,speed:'normal',audio_asset_id:AID}
 assert.equal(validateVoiceSelection(uploaded,{shopId:SHOP,approvedAudioAssets:assets}).audio_asset_id,AID)
 assert.throws(()=>validateVoiceSelection(uploaded,{shopId:SHOP,approvedAudioAssets:[
  {id:AID,shop_id:CAM,kind:'audio',authorized:true}
 ]}))
 assert.throws(()=>makeVoiceAction({selection:uploaded,shopId:SHOP,campaignId:CAM,
   planSha256:SHA,userConfirmedCharge:true,idempotencyKey:ID,approvedAudioAssets:assets}))
})
test('foreign voice and style, forged booleans, extra keys, missing spend opt-in denied',()=>{
 for(const wrong of [
  {...ai,voice_id:'en-US-BadNeural'},
  {...ai,language:'hi-IN'},
  {...ai,speed:'200%'},
  {...ai,shop_id:SHOP},
 ])assert.throws(()=>validateVoiceSelection(wrong,{shopId:SHOP}))
 for(const confirmed of [undefined,false,'true'])
   assert.throws(()=>makeVoiceAction({selection:ai,shopId:SHOP,campaignId:CAM,
    planSha256:SHA,userConfirmedCharge:confirmed,idempotencyKey:ID}))
 assert.throws(()=>makeVoiceAction({selection:ai,shopId:SHOP,campaignId:CAM,
    planSha256:SHA,userConfirmedCharge:true,idempotencyKey:'fake'}))
})

test('private upload receipt cannot survive same-metadata File replacement or source switch',()=>{
 const original={name:'narration.wav',size:4096,lastModified:100,mime:'audio/wav'}
 const replacement={...original}
 const scope=SHOP+':'+CAM+':'+SHA+':reviewed-script'
 const current={submittedFile:original,currentFile:original,
   submittedScope:scope,currentScope:scope}
 assert.equal(isCurrentPrivateUpload(current),true)
 assert.equal(isCurrentPrivateUpload({...current,currentFile:replacement}),false)
 assert.equal(isCurrentPrivateUpload({...current,currentScope:scope+':revised'}),false)
 assert.equal(isCurrentPrivateUpload({...current,submittedFile:null}),false)
 assert.equal(isCurrentPrivateUpload({...current,submittedScope:''}),false)
})
