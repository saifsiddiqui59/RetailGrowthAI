/**
 * Feature7 offline intake -> semantic decision package.
 *
 * This trusted-worker helper deliberately does NOT implement Auth/JWT/RLS,
 * public upload, transcript inference, approvals, clip editing or rendering.
 * Its inputs MUST come from a server-authorized private rights snapshot and
 * already-generated WhisperX JSON bound to each exact private video hash.
 * No content leaves the worker. Synthetic data can exercise the full pipeline.
 */
import {verifyPrivateVideo,resolveApprovedLocalVideo} from './media_preflight.mjs';
import {normalizeWhisperx} from './transcript_adapter.mjs';
import {analyzeLocalAudioActivity} from './audio_activity.mjs';
import {proposeUploadedFootageEdits,EditValidationError} from './autobroll_semantics.mjs';
import {suggestRetakeSelections,suggestOwnedCutaways} from './semantic_suggestions.mjs';
import {suggestGapCuts} from './gap_cut_advisory.mjs';
import {analyzeLocalVisualActivity} from './visual_activity.mjs';

export function preparePrivateReview({shop_id,campaign_id,draft,root,media,
  broll_grants=[],include_visual_qa=false}={}) {
  if(!draft || draft.shop_id!==shop_id || draft.campaign_id!==campaign_id ||
    !Array.isArray(draft.scenes) || !Array.isArray(media) ||
    draft.scenes.length!==media.length || !Array.isArray(broll_grants) ||
    broll_grants.length>24)
    throw new EditValidationError('Invalid trusted-review identity or scene count');
  const approvedFootage=[];
  const grants=[];
  const evidence=[];
  for(let index=0;index<media.length;index++) {
    const item=media[index];
    if(!item || item.scene_index!==index || item.asset_id!==draft.scenes[index]?.asset_id)
      throw new EditValidationError('Unmatched source scene/asset binding');
    const verified=verifyPrivateVideo({shop_id,asset_id:item.asset_id,
      grant:item.grant,root,relative_path:item.relative_path,
      expected_sha256:item.expected_sha256});
    const transcript=normalizeWhisperx({asset_id:item.asset_id,shop_id,
      source_sha256:verified.sha256,source_duration_seconds:verified.duration_seconds,
      transcript:item.whisperx_json});
    if(item.grant.has_audio!==verified.has_audio)
      throw new EditValidationError('Authorized audio metadata mismatch');
    const activity=verified.has_audio
      ? analyzeLocalAudioActivity({path:resolveApprovedLocalVideo({
          root,relative_path:item.relative_path}),
        duration_seconds:verified.duration_seconds,has_audio:true})
      : {silence_intervals:[],non_silent_intervals:[],
        classification:'NO_AUDIO_TRACK',original_audio_preserved:true};
    // This is only an objective contradiction check. FFmpeg activity is NOT
    // human-speech VAD or ASR provenance: real model accuracy still needs
    // independently signed private-worker evidence and human listening.
    if(transcript.words.length>0 &&
      (!verified.has_audio || activity.non_silent_intervals.length===0))
      throw new EditValidationError(
        'Supplied speech words contradict absent or entirely silent source audio');
    grants.push({...item.grant,asset_id:item.asset_id,
      shop_id,media_type:'video',has_audio:verified.has_audio});
    approvedFootage.push({
      scene_index:index,asset_id:item.asset_id,
      source_duration_seconds:verified.duration_seconds,
      has_audio:verified.has_audio,transcription_status:transcript.transcription_status,
      transcript_sha256:transcript.transcript_sha256,
      words:transcript.words,broll_candidates:item.broll_candidates??[]
    });
    evidence.push({scene_index:index,asset_id:item.asset_id,
      source_sha256:verified.sha256,transcript_sha256:transcript.transcript_sha256,
      source_duration_seconds:verified.duration_seconds,
      local_media_verified:verified.validation,audio_activity:activity,
      visual_activity:include_visual_qa ? analyzeLocalVisualActivity({
        path:resolveApprovedLocalVideo({root,relative_path:item.relative_path}),
        duration_seconds:verified.duration_seconds}) : null,
      container:'video/mp4',paid_calls:0});
  }
  // Check B-roll as trusted same-shop reviewed retailer uploads too. No URL,
  // preview token, Pexels search, dynamic asset or outbound request is allowed.
  for(const g of broll_grants) grants.push(g);
  const proposal=proposeUploadedFootageEdits({
    shop_id,campaign_id,draft,footage:approvedFootage,grants
  });
  const silence_jump_cut_advisory=approvedFootage.map(f=>suggestGapCuts({
    asset_id:f.asset_id,source_scene_index:f.scene_index,words:f.words,
    source_duration_seconds:f.source_duration_seconds,
    target_duration_seconds:draft.scenes[f.scene_index].duration
  }));
  const retakes_advisory=suggestRetakeSelections({shop_id,
    footage:approvedFootage.map(f=>({...f,shop_id}))});
  const owned_cutaways_advisory=approvedFootage.flatMap(f=>
    suggestOwnedCutaways({shop_id,words:f.words,
      approved_assets:broll_grants,max_cues:3}).map(c=>({
        ...c,source_scene_index:f.scene_index
      })));
  return {...proposal,media_evidence:evidence,
    retakes_advisory,owned_cutaways_advisory,silence_jump_cut_advisory,
    review_status:'NEEDS_REVIEW',approved:false,renderable:false,
    media_approval_is_not_human_edit_approval:true};
}
