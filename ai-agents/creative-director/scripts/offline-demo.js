#!/usr/bin/env node
'use strict';

// Offline DEMO only: genuine pinned MIT Kuble plan/compiler/caption source.
// All "rights" and "approved offers" inside this fixture are fabricated for
// unit tests and must never be used for a shop, provider or advertisement.
const {compile}=require('../director');
const {captionsFromApprovedDirectorTiming}=require('../caption-preview');
const {verifiedBrief,authoredCandidate}=require('../tests/fixtures/diwali-premium-fixture');
function main(args){
  if(args.length!==2||!['15','30','60'].includes(args[0])||
     !['--summary','--json'].includes(args[1])){
    throw new Error('Usage: node offline-demo.js 15|30|60 --summary|--json');
  }
  const seconds=Number(args[0]),request=verifiedBrief(seconds);
  const authored=authoredCandidate(seconds);
  const words=authored.voiceover_script.split(/\s+/).map((text,i)=>({
    text,start:i*.15,end:(i+1)*.15,
  }));
  const bundle=compile(request,authored,{actual_voice_alignment:{
    words,duration:words.length*.15,
  }});
  const captionPreview=captionsFromApprovedDirectorTiming(bundle);
  if(bundle.approval_record.approved!==false||
     bundle.approval_record.can_publish!==false||
     bundle.approval_record.can_run_paid_motion!==false||
     captionPreview.can_start_gpu!==false)
    throw new Error('Synthetic demonstration must be a nonpublishable DRAFT');
  const manifest={
    origin:'SYNTHETIC_FIXTURE_ONLY_NOT_ACTUAL_RETAILER_APPROVAL',
    upstream:'Kuble-Lab/open-creative-director',
    upstream_pin:'4ab1a40d15ee8c1a1427c092dce08dc7dfbefa6f',
    output_kind:'SOURCE_ONLY_UNLICENSED_PREVIEW_NOT_VIDEO',
    shop_id:request.shop_id,
    campaign_id:request.campaign_id,
    duration_seconds:seconds,
    full_hd_target:'1080x1920 portrait not rendered',
    scenes:bundle.creative_direction_v1.scenes.length,
    motion_shots:bundle.motion_direction_v1.length,
    caption_lines:captionPreview.subtitles.length,
    caption_source_original_upstream:captionPreview.source_library,
    editorial_plan_sha256:bundle.approval_record.plan_sha256,
    rights_evidence_real:false,
    original_stock_video_downloaded:false,
    narrator_real_speech_verified:false,
    model_generated:false,
    video_rendered:false,
    gpu_enabled:false,
    billed_calls:0,
    can_publish:false,
    can_dispatch_paid_motion:false,
  };
  return args[1]==='--summary'?manifest:{
    ...manifest,bundle,caption_preview:captionPreview,
  };
}
if(require.main===module){
  try{
    process.stdout.write(JSON.stringify(main(process.argv.slice(2)))+'\n');
  }catch(e){
    process.stderr.write('Feature2 offline demo denied: '+e.message+'\n');
    process.exitCode=2;
  }
}
module.exports={main};
