/**
 * Stock Pexels rights/provenance fixture used ONLY to test AutoBroll's
 * editing suggestions (which were already adapted under the upstream MIT
 * license in autobroll_semantics.mjs). Never label this as a retailer upload.
 *
 * No Pexels API keys, unapproved downloads, fake current-member grants, or
 * customer advertising approval are created by this module.
 */
import {buildCaptions,speechRuns,EditValidationError} from './autobroll_semantics.mjs';

export const PEXELS_STOCK_FIXTURE=Object.freeze({
  fixture_only:true,
  site:'Pexels',
  license_url:'https://www.pexels.com/license/',
  user_approved_customer_asset:false,
  person_or_brand_endorsement:false,
  video:Object.freeze({
    id:'pexels-8581174',
    page:'https://www.pexels.com/video/clothes-hanging-on-a-rack-8581174/',
    download:'https://www.pexels.com/download/video/8581174/',
    downloaded_media_host:'videos.pexels.com',
    creator:'RDNE Stock project',media_kind:'video',
    has_independently_verified_speech:false
  }),
  image:Object.freeze({
    id:'pexels-5490963',
    page:'https://www.pexels.com/photo/assorted-colorful-clothes-hanging-on-rack-in-store-5490963/',
    download:'https://images.pexels.com/photos/5490963/pexels-photo-5490963.jpeg?cs=srgb&dl=pexels-rachel-claire-5490963.jpg&fm=jpg',
    downloaded_media_host:'images.pexels.com',
    creator:'Rachel Claire',media_kind:'image'
  })
});

/**
 * Adapted from AutoBroll's source-relative phrase-aware caption grouping
 * and stock B-roll preview semantics, pinned in AUTOBROLL_MIT_LICENSE.txt.
 * The phrases here are TEST-ONLY authored marketing text, NOT
 * WhisperX audio transcripts or claims about actual boutique inventory.
 * F4 is sole production renderer; returns no executable or approved edit.
 */
export function buildPexelsOfflineEditFixture({
  shop_id='demo-stock-shop',campaign_id='pexels-offline-demo',
  video_asset_id='pexels-8581174',image_asset_id='pexels-5490963',
  original_video_duration=10,video_segment_seconds=4,
  image_segment_seconds=3,fade_seconds=0.5
}={}){
  const identity=/^[A-Za-z0-9_-]{1,120}$/;
  for(const id of [shop_id,campaign_id,video_asset_id,image_asset_id]){
    if(typeof id!=='string'||!identity.test(id))
      throw new EditValidationError('Invalid demo media or tenant id');
  }
  if(![original_video_duration,video_segment_seconds,
    image_segment_seconds,fade_seconds].every(Number.isFinite) ||
    original_video_duration<video_segment_seconds ||
    video_segment_seconds<2 ||video_segment_seconds>10 ||
    image_segment_seconds<1 ||image_segment_seconds>6 ||
    fade_seconds<=0 ||fade_seconds>1 ||
    fade_seconds>=Math.min(video_segment_seconds,image_segment_seconds))
    throw new EditValidationError('Invalid Pexels stock edit timing');
  const marketingWords=[
    {word:'Fresh',startMs:300,endMs:650},
    {word:'styles.',startMs:700,endMs:1120},
    {word:'Browse',startMs:1500,endMs:1800},
    {word:'today.',startMs:1850,endMs:2250}
  ];
  // Reuses verified AutoBroll algorithm, no new caption planning engine.
  const pages=buildCaptions(marketingWords,video_asset_id);
  // Stock clip contains no independently verified spoken audio; never run
  // actual speech cuts from fictional marketing text.
  const speechCuts=speechRuns([],original_video_duration);
  if(speechCuts.length!==0)throw new EditValidationError('Synthetic audio transcript not allowed');
  return Object.freeze({
    shop_id,campaign_id,upstream:'andriidrok1/autobroll',
    upstream_license:'MIT',source_review_required:true,
    voice_transcription_claimed:false,real_user_approval:false,
    gpu_required:false,paid_provider_calls:0,
    video_asset_id,image_asset_id,
    video_segment_seconds,image_segment_seconds,fade_seconds,
    expected_duration_seconds:video_segment_seconds+image_segment_seconds-fade_seconds,
    marketing_overlay_pages:pages.map(x=>({...x,marketing_text_only:true})),
    source_relative_speech_runs:[],
    output_type:'TEMPORARY_OFFLINE_TEST_PREVIEW',
    editor_implementation:'EXISTING_AUTOBROLL_ALGORITHM_AND_FFMPEG_TEST_HARNESS',
    production_feature4_editor_unchanged:true
  });
}
