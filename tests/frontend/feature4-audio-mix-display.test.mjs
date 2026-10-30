import test from 'node:test'
import assert from 'node:assert/strict'
import { fixedAudioMixDisplay } from '../../frontend/src/features/video/audio-mix-display.mjs'

const SHOP = '11111111-1111-4111-8111-111111111111'
const OTHER = '22222222-2222-4222-8222-222222222222'
const music = [{id:'song',shop_id:SHOP,kind:'audio',authorized:true},
  {id:'voice',shop_id:SHOP,kind:'audio',authorized:true}]
const media = [{id:'photo',shop_id:SHOP,kind:'image',authorized:true},
  {id:'clip',shop_id:SHOP,kind:'video',authorized:true},
  {id:'foreign',shop_id:OTHER,kind:'video',authorized:true}]
const draft = (scene = {asset_id:'photo'}) => ({
  shop_id:SHOP,music_asset_id:'song',voiceover_asset_id:null,
  scenes:[scene],duration_seconds:30,
})

test('silent/still-only mix is fixed at renderer 55%, never editable', () => {
  const result = fixedAudioMixDisplay(draft(),media,music)
  assert.equal(result.music,true)
  assert.equal(result.musicGain,0.55)
  assert.equal(result.musicGainVerifiedByBrowser,false)
  assert.equal(result.musicGainUnknownUntilServerProbe,false)
  assert.equal(result.sceneSfxGain,0.25)
  assert.equal(result.sceneSfxMaximumSeconds,2)
})

test('narration forces renderer 12% bed, independent of video source sound', () => {
  for(const scene of [{asset_id:'photo'},{asset_id:'clip'}]){
    const result = fixedAudioMixDisplay({...draft(scene),voiceover_asset_id:'voice'},media,music)
    assert.equal(result.narration,true)
    assert.equal(result.narrationGain,1)
    assert.equal(result.musicGain,0.12)
  }
})

test('unmuted video makes browser music gain unknown until trusted ffprobe', () => {
  const result = fixedAudioMixDisplay(draft({asset_id:'clip'}),media,music)
  assert.equal(result.musicGain,null)
  assert.equal(result.musicGainUnknownUntilServerProbe,true)
  assert.equal(result.musicGainVerifiedByBrowser,false)
})

test('muted video and unauthorized video cannot invent source-audio ducking', () => {
  assert.equal(fixedAudioMixDisplay(draft({asset_id:'clip',mute_source:true}),media,music).musicGain,0.55)
  assert.equal(fixedAudioMixDisplay(draft({asset_id:'foreign'}),media,music).musicGain,0.55)
  assert.equal(fixedAudioMixDisplay(draft({asset_id:'clip'}),media.map(a=>a.id==='clip'?{...a,authorized:false}:a),music).musicGain,0.55)
})

test('foreign or revoked audio never yields an apparent licensed gain', () => {
  for(const row of [{...music[0],shop_id:OTHER},{...music[0],authorized:false}]){
    const result = fixedAudioMixDisplay(draft(),media,[row,music[1]])
    assert.equal(result.music,false)
    assert.equal(result.musicGain,null)
    assert.equal(result.musicGainUnknownUntilServerProbe,false)
  }
  assert.equal(fixedAudioMixDisplay({...draft(),voiceover_asset_id:'voice'},media,
    [{...music[0]},{...music[1],shop_id:OTHER}]).narration,false)
})

test('absence of a soundtrack is distinct from unknown soundtrack gain', () => {
  const result = fixedAudioMixDisplay({...draft({asset_id:'clip'}),music_asset_id:null},media,music)
  assert.equal(result.music,false)
  assert.equal(result.musicGain,null)
  assert.equal(result.musicGainUnknownUntilServerProbe,false)
})
