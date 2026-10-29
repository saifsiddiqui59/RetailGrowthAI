'use strict';
// Actual pinned MIT director + existing synthetic fixture -> nonpublishable F4/F5 input.
const {compile}=require('./director');
const {previewOffline}=require('./offline-acceptance');
const {verifiedBrief,authoredCandidate}=require('./tests/fixtures/diwali-premium-fixture');
const {createHash}=require('node:crypto');
const {readFileSync}=require('node:fs');
const {resolve}=require('node:path');
const hash=s=>createHash('sha256').update(s).digest('hex');
function exportFixture(duration){
  if(![15,30,60].includes(duration)) throw Error('Unsupported source-only test duration');
  const input=verifiedBrief(duration);
  const bundle=compile(input,authoredCandidate(duration));
  return exportCompiled(bundle,input,duration);
}
// Use the exact output of the *same* actual MIT director call that the
// signed-source Python/Node integration just validated. Do not compile
// a second synthetic fixture in that cross-feature test.
function exportCompiled(bundle,input,duration){
  if(![15,30,60].includes(duration)||!input||typeof input!=='object'||
    input.server_verified!==true||input.authenticated_owner_or_editor!==true||
    !Array.isArray(input.media_grants)||input.media_grants.length!==1||
    input.media_grants[0]?.shop_id!==input.shop_id||
    input.media_grants[0]?.original_media_sha256?.length!==64||
    bundle?.creative_direction_v1?.shop_id!==input.shop_id||
    bundle?.creative_direction_v1?.campaign_id!==input.campaign_id||
    bundle?.creative_direction_v1?.duration_seconds!==duration||
    !Array.isArray(bundle?.motion_direction_v1)||
    bundle?.motion_direction_v1?.some(m=>
      m.reference_media_id!==input.media_grants[0].id ||
      m.product_sku!==input.media_grants[0].product_sku ||
      Object.keys(input.media_grants[0].garment_facts||{}).some(k=>
        m.garment_lock?.[k]!==input.media_grants[0].garment_facts[k])))
    throw Error('Compiled director plan and original media scope mismatch');
  const checked=previewOffline(bundle,{gpuEnabled:false});
  const original=bundle.creative_direction_v1, motion=bundle.motion_direction_v1;
  if(checked.billable_calls!==0||checked.generated_video_files!==0||
    checked.can_publish!==false||motion.length!==duration/5)
    throw Error('Original director acceptance not trusted');
  const src=JSON.parse(readFileSync(resolve(__dirname,
    '../test-fixtures/clothing-shop-pexels/manifest.json'),'utf8'));
  if(src.fixture_kind!=='PUBLIC_SOURCE_REFERENCES_ONLY_NOT_IMPORTED_ASSETS'||
    src.source_media.length!==4||src.source_media.some(x=>
      x.original_sha256!==null||x.private_storage_ref!==null))
    throw Error('Unexpected approved stock media in fixture');
  let second=0;
  const timeline=[],requests=[],cues=[];
  for(let i=0;i<motion.length;i++){
    const m=motion[i],s=original.scenes.find(x=>x.id===m.scene_id);
    if(!s||s.shots.length!==1||s.shots[0].shot_id!==m.shot_id||
      m.shot_start_seconds!==second||m.duration_seconds!==5||
      s.duration_seconds!==5||m.generation_prompt.length<400||
      checked.editor_timeline[i].original_generation_prompt_sha256!==hash(m.generation_prompt))
      throw Error('Compiler/shot mismatch');
    for(const trait of Object.values(input.media_grants[0].garment_facts))
      if(!m.generation_prompt.toLowerCase().includes(trait.toLowerCase()))
        throw Error('Original motion prompt lost garment identity');
    const digest=hash(m.generation_prompt);
    timeline.push({shot_id:m.shot_id,scene_id:m.scene_id,start_seconds:second,
      duration_seconds:5,role:s.role,overlay_text:s.role==='cta'?original.cta:'',
      voiceover_text:s.voiceover,dialogue_text:s.dialogue,
      transition_out:s.transition_out,camera:m.camera,lighting:m.lighting,
      garment_lock:m.garment_lock,immutable_motion_prompt_sha256:digest,
      asset_id:null,asset_status:'REQUIRES_REAL_F3_OR_F5_APPROVED_PRIVATE_MEDIA',
      ready_to_render:false});
    requests.push({shot_id:m.shot_id,scene_id:m.scene_id,start_seconds:second,
      duration_seconds:5,original_direction:m,original_prompt_sha256:digest,
      first_frame_asset_id:null,first_frame_sha256:null,
      native_wan_profile:{model:'wan22_ti2v_5b_comfy_v1',
        width:704,height:1280,fps:24,frames:121},
      provider_call_permitted:false,gpu_enabled:false,cost_reserved:false,
      ready_for_feature5_lease:false});
    cues.push({shot_id:m.shot_id,start_seconds:second,duration_seconds:5,
      voiceover_text:s.voiceover,dialogue_text:s.dialogue,
      real_speech_audio_verified:false});
    second+=5;
  }
  if(second!==duration) throw Error('Gapped original director timeline');
  return {schema:'retailgrowth.feature2-f4-f5-offline-fixture.v1',
    source_engine:'pinned MIT Kuble-Lab Open Creative Director',
    scenario:'Thread and Loom fictional Diwali kurti',
    shop_id:'SYNTHETIC_NOT_REAL_OWNER',
    original_fixture_shop_id:input.shop_id,
    original_fixture_campaign_id:input.campaign_id,
    duration_seconds:duration,
    source_plan_sha256:bundle.approval_record.plan_sha256,
    garment_facts:input.media_grants[0].garment_facts,
    synthetic_discount:'20% off selected kurtis - TEST ONLY NOT RETAILER APPROVED',
    source_media:{candidates:src.source_media.map(x=>({
      id:x.candidate_id,type:x.media_type,page:x.source_page,
      creator:x.creator,sha256:null,private_asset_id:null,
      can_claim_retailer_product:false})),
      feature3_authoritative_consumer_source:'poster-engine/feature3_consumer_packets_v1.py',
      approved_feature3_frame_present:false},
    feature4:{target:{width:1080,height:1920,fps:24,video_codec:'h264',
        audio_codec:'aac'},timeline,approved_render_request:null,
      ready_to_render_customer_reel:false},
    feature5:{native_output_not_full_hd:true,clip_requests:requests,
      can_run_paid_motion:false,approved_feature3_first_frame_present:false,
      gpu_enabled:false},
    audio:{voiceover_script:original.voiceover_script,
      narration_cues:cues,track_id:null,licensed_music_bytes_present:false,
      voiceover_audio_bytes_present:false,real_word_sync_verified:false,
      can_mix_music:false},
    review:{status:'SYNTHETIC_DRAFT',signed_customer_approval:false,
      licensed_media_approval:false,approved_product_or_model:false,
      owner_confirmed_offer:false,can_publish:false,
      paid_calls:0,hosted_reel_rendered:false}};
}
if(require.main===module){
  if(process.argv.length!==3||!/^(15|30|60)$/.test(process.argv[2])){
    process.stderr.write('Usage: node export-feature4-feature5-fixture.js 15|30|60\n');
    process.exit(2);
  }
  process.stdout.write(JSON.stringify(exportFixture(Number(process.argv[2])),null,2)+'\n');
}
module.exports={exportFixture,exportCompiled};
