// Only bytes, hashes, binding and browser policy are tested: NOT speech.
import test from 'node:test'
import assert from 'node:assert/strict'
import crypto from 'node:crypto'
import {verifyLocalPrivatePlayback} from '../../frontend/src/features/voiceover/voiceover-private-playback.mjs'
const shop='11111111-1111-4111-8111-111111111111'
const campaign='22222222-2222-4222-8222-222222222222'
const audioId='33333333-3333-4333-8333-333333333333'
const bytes=new Uint8Array(128)
bytes.set(Buffer.from('RIFF'),0)
bytes.set(Buffer.from('WAVE'),8)
const digest=crypto.createHash('sha256').update(bytes).digest('hex')
function fixtures() {
  return {
    shopId:shop,campaignId:campaign,
    receipt:{shop_id:shop,campaign_id:campaign,provider:'kokoro-onnx',
      private:true,can_publish:false,private_audio_asset_id:audioId,
      original_audio_sha256:digest},
    readResult:{shop_id:shop,campaign_id:campaign,asset_id:audioId,
      original_audio_sha256:digest,private:true,mime_type:'audio/wav',
      audio_bytes:bytes}
  }
}
test('Original private WAV hash and source binding pass; no audio quality claim',async()=>{
  const s=await verifyLocalPrivatePlayback(fixtures())
  assert.equal(s.sha256,digest)
  assert.equal(s.bytes.length,128)
})
for(const name of ['cross-shop','wrong-asset','altered-bytes','public','forged-hash','wrong-mime','huge','no-confirmed-original']) {
  test('Rejects '+name,async()=>{
    const p=fixtures()
    if(name==='cross-shop')p.readResult.shop_id='foreign'
    if(name==='wrong-asset')p.readResult.asset_id='foreign'
    if(name==='altered-bytes'){p.readResult.audio_bytes=new Uint8Array(bytes);p.readResult.audio_bytes[20]=4}
    if(name==='public')p.readResult.private=false
    if(name==='forged-hash')p.receipt.original_audio_sha256='0'.repeat(64)
    if(name==='wrong-mime')p.readResult.mime_type='audio/mpeg'
    if(name==='huge')p.readResult.audio_bytes=new Uint8Array(20_000_001)
    if(name==='no-confirmed-original')p.receipt.can_publish=true
    await assert.rejects(()=>verifyLocalPrivatePlayback(p))
  })
}
