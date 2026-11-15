'use strict';

// Cross-PR source compatibility gate against actual draft F4 PR #322.
// Never authorizes F4/F5 execution or bypasses outbox, media, billable gate.
const { editorHandoff } = require('./handoff-approval');
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const F4_PRESENT_SOURCE = Object.freeze({
  pr: 322,
  motion_file: 'video-engine/feature4_motion_handoff.py',
  composition_file: 'video-engine/creative_contract.py',
  accepted_motion_model: 'hunyuanvideo-1.5-480p',
  accepted_motion_duration_seconds: 5,
  accepted_motion_prompt_max: 1500,
  accepted_shots_max: 12,
  accepts_feature2_wan_motion_direction_v1: false
});
function auditFeature4Consumer(bundle, receipt, key, shopId) {
  const handoff = editorHandoff(bundle, receipt, key, shopId);
  const issues = [];
  const shots = handoff.motion_direction_v1;
  const creative = handoff.creative_direction_v1;
  if (!UUID.test(creative.shop_id) || !UUID.test(creative.campaign_id)) {
    issues.push('F4_REQUIRES_UUID_SHOP_CAMPAIGN_IDENTIFIERS');
  }
  if (shots.length > F4_PRESENT_SOURCE.accepted_shots_max ||
      shots.some(s => s.duration_seconds !== F4_PRESENT_SOURCE.accepted_motion_duration_seconds)) {
    issues.push('F4_ONLY_1_TO_12_EXACT_FIVE_SECOND_MOTION_SHOTS');
  }
  if (shots.some(s => !UUID.test(s.reference_media_id))) {
    issues.push('F4_REQUIRES_SIGNED_UUID_FEATURE3_MEDIA_IDS');
  }
  if (shots.some(s => typeof s.generation_prompt !== 'string' ||
      s.generation_prompt.length > F4_PRESENT_SOURCE.accepted_motion_prompt_max)) {
    issues.push('F4_V1_MOTION_PROMPT_LIMIT_1500_NEVER_TRUNCATE');
  }
  if (shots.some(s => s.requested_profile?.kind !== 'image_to_video')) {
    issues.push('F4_REQUIRES_EXPLICIT_MOTION_SOURCE_TYPE');
  }
  // F4 currently requires a different signed direction with F2 source_feature,
  // approved flag, approval UUID, separate exact nine-field motion_direction_v1,
  // and independently server-fetched rights-approved media snapshot. Projection
  // and final model profile must be coordinator-ratified, not silently guessed.
  issues.push('F4_REVIEWED_SOURCE_DIRECTION_SHAPE_IS_DIFFERENT');
  issues.push('F4_REQUIRES_INDEPENDENT_SERVER_FETCHED_MEDIA_APPROVAL_SNAPSHOT');
  issues.push('F4_CURRENT_F5_PROFILE_IS_HUNYUAN_480P_NOT_APPROVED_WAN_2_2');
  return {
    contract: 'feature2_to_feature4_compatibility_audit_v1',
    source_pr: 514, target_pr: F4_PRESENT_SOURCE.pr,
    current_feature5_model_profile: F4_PRESENT_SOURCE.accepted_motion_model,
    approved_creative_sha256: receipt.plan_sha256,
    may_publish: false, may_queue_paid_motion: false, may_render_as_wan: false,
    compatibility: 'BLOCKED_UNTIL_CONSUMER_INTERFACE_RATIFIED',
    issues: [...new Set(issues)]
  };
}
module.exports = { auditFeature4Consumer, F4_PRESENT_SOURCE };
