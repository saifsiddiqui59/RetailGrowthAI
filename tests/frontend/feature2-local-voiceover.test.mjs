import test from 'node:test'
import assert from 'node:assert/strict'
import {F2_LOCAL_VOICES, makeLocalVoiceAction} from '../../frontend/src/features/voiceover/voiceover-model.mjs'
const SHOP='11111111-1111-4111-8111-111111111111'
const CID='22222222-2222-4222-8222-222222222222'
const UUID='33333333-3333-4333-8333-333333333333'
const source={shopId:SHOP,campaignId:CID,planSha256:'a'.repeat(64),
 idempotencyKey:UUID,voiceId:'af_heart',lang:'en-us',speed:'normal',preview:false}
test('actual Kokoro ONNX v1 English voices only, no false Hindi Marathi',()=>{
 assert.equal(F2_LOCAL_VOICES.length,8)
 assert.deepEqual(new Set(F2_LOCAL_VOICES.map(x=>x.locale)),new Set(['en-us','en-gb']))
})
test('local voice source action is free only with operator validation pending',()=>{
 const packet=makeLocalVoiceAction(source)
 assert.equal(packet.estimated_paid_cost_usd,0)
 assert.equal(packet.provider,'kokoro-onnx')
 assert.equal(packet.needs_current_server_signed_grants,true)
 assert.equal(packet.may_auto_invoke_azure,false)
})
test('cross-language, forged voice, invalid speed and weak tenant denied',()=>{
 for(const changes of [{lang:'hi-in'},{lang:'mr-in'},
   {voiceId:'hi-IN-SwaraNeural'},{speed:'2.0'},
   {shopId:CID.replaceAll('2','z')}])
    assert.throws(()=>makeLocalVoiceAction({...source,...changes}))
})
