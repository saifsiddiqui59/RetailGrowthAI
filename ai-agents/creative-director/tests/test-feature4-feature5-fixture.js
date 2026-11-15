'use strict';
const assert=require('node:assert/strict');
const {exportFixture}=require('../export-feature4-feature5-fixture');
const {createHash}=require('node:crypto');
for(const duration of [15,30,60]){
  const a=exportFixture(duration),b=exportFixture(duration);
  assert.equal(JSON.stringify(a),JSON.stringify(b));
  assert.equal(a.schema,'retailgrowth.feature2-f4-f5-offline-fixture.v1');
  assert.equal(a.review.can_publish,false);
  assert.equal(a.review.signed_customer_approval,false);
  assert.equal(a.feature5.gpu_enabled,false);
  assert.equal(a.audio.licensed_music_bytes_present,false);
  assert.equal(a.source_media.approved_feature3_frame_present,false);
  assert.equal(a.feature4.timeline.length,duration/5);
  assert.equal(a.feature5.clip_requests.length,duration/5);
  assert.equal(a.audio.narration_cues.length,duration/5);
  assert.equal(a.source_media.candidates.length,4);
  for(let i=0;i<duration/5;i++){
    const s=a.feature4.timeline[i],m=a.feature5.clip_requests[i];
    assert.equal(s.start_seconds,5*i);
    assert.equal(s.duration_seconds,5);
    assert.equal(m.start_seconds,s.start_seconds);
    assert.equal(m.shot_id,s.shot_id);
    assert.equal(s.immutable_motion_prompt_sha256,m.original_prompt_sha256);
    assert.equal(m.original_prompt_sha256,
      createHash('sha256').update(m.original_direction.generation_prompt).digest('hex'));
    assert.equal(m.native_wan_profile.width,704);
    assert.equal(m.native_wan_profile.height,1280);
    assert.equal(m.native_wan_profile.frames,121);
    assert.equal(m.first_frame_asset_id,null);
    assert.equal(m.first_frame_sha256,null);
    assert.equal(s.asset_id,null);
    assert.equal(m.provider_call_permitted,false);
    for(const value of Object.values(a.garment_facts))
      assert.ok(m.original_direction.generation_prompt.toLowerCase().includes(value.toLowerCase()));
  }
  assert.equal(a.feature4.timeline[0].role,'hook');
  assert.equal(a.feature4.timeline.at(-1).role,'cta');
  assert.equal(a.feature4.timeline.at(-1).overlay_text,a.feature4.timeline.at(-1).overlay_text);
}
assert.throws(()=>exportFixture(20),/Unsupported/);
console.log('ACTUAL MIT compiler F2->F4/F5 15/30/60s input export PASS, $0 GPU OFF');
