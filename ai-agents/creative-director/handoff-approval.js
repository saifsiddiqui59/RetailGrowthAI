'use strict';

// Feature2 -> Feature4/5 offline, server-side-only creative approval receipt.
// Requires a trusted current JWT/RLS reviewer and HMAC secret OUTSIDE browser.
// Approval is editorial only; never grants Feature5 model cost or publishing.
const crypto = require('node:crypto');
function reject(message) { throw new Error('CREATIVE_HANDOFF_REJECTED: ' + message); }
function hash(data) { return crypto.createHash('sha256').update(JSON.stringify(data)).digest('hex'); }
function id(value) { return typeof value === 'string' && /^[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}$/.test(value); }
function guardKey(key) {
  if (!Buffer.isBuffer(key) && typeof key !== 'string') reject('Server secret unavailable');
  if (Buffer.byteLength(key) < 32) reject('Weak or missing server-held approval signing key');
}
function expectedPlanSha(bundle) {
  if (!bundle || typeof bundle !== 'object' || !bundle.creative_direction_v1 ||
      !Array.isArray(bundle.motion_direction_v1) || !bundle.approval_record) reject('Missing versioned creative bundle');
  const creative = bundle.creative_direction_v1;
  if (creative.contract !== 'creative_direction_v1' || creative.version !== 1 ||
      creative.source_generated_media !== false || creative.provider_output_guaranteed !== false ||
      !Array.isArray(creative.reference_media_requests) || !creative.reference_media_requests.length ||
      !Array.isArray(creative.scenes) || !creative.scenes.length) reject('Invalid creative source contract');
  if (bundle.motion_direction_v1.some(m => !m || m.contract !== 'motion_direction_v1' ||
      m.shop_id !== creative.shop_id || m.campaign_id !== creative.campaign_id ||
      m.requested_profile?.inference_approved !== false)) reject('Invalid or already-active motion source');
  const source_media = creative.reference_media_requests.map(req => {
    const matching = bundle.motion_direction_v1.find(m => m.reference_media_id === req.asset_id);
    if (!matching || req.same_shop_required !== true || req.rights_review_required !== true ||
        !matching.garment_lock) reject('Missing approved source garment lineage');
    return matching.garment_lock;
  });
  const fingerprint = hash({ creative, source_media });
  if (bundle.approval_record.plan_sha256 !== fingerprint ||
      bundle.approval_record.review_status !== 'DRAFT' ||
      bundle.approval_record.approved !== false ||
      bundle.approval_record.can_publish !== false ||
      bundle.approval_record.can_run_paid_motion !== false) reject('Forged or already mutable draft');
  return fingerprint;
}
function payloadOf(planSha, motionSha, shopId, campaignId, reviewerId, timestamp) {
  return { plan_sha256: planSha, motion_sha256: motionSha, shop_id: shopId, campaign_id: campaignId,
    reviewer_id: reviewerId, approved_at_utc: timestamp,
    decision: 'CREATIVE_ONLY_APPROVED_NOT_PUBLISHED',
    can_publish: false, can_run_paid_motion: false };
}
function signatureOf(payload, key) {
  return crypto.createHmac('sha256', key).update(JSON.stringify(payload)).digest('hex');
}
function approveCreativeDraft(bundle, reviewer, secretKey) {
  guardKey(secretKey);
  const creative = bundle.creative_direction_v1;
  if (!reviewer || reviewer.server_verified !== true ||
      reviewer.current_member !== true || reviewer.shop_id !== creative.shop_id ||
      !['OWNER', 'EDITOR'].includes(reviewer.role) || !id(reviewer.id) ||
      reviewer.completed_claims_review !== true || reviewer.completed_media_rights_review !== true ||
      reviewer.completed_storyboard_review !== true || reviewer.completed_script_review !== true)
    reject('Current RLS-authorized human reviewer and all editorial checks required');
  const fingerprint = expectedPlanSha(bundle);
  const payload = payloadOf(fingerprint, hash(bundle.motion_direction_v1), creative.shop_id, creative.campaign_id,
    reviewer.id, new Date().toISOString());
  return { ...payload, hmac_sha256: signatureOf(payload, secretKey) };
}
function verifyCreativeApproval(bundle, receipt, secretKey, expectedShop) {
  guardKey(secretKey);
  const sha = expectedPlanSha(bundle);
  const creative = bundle.creative_direction_v1;
  // The HMAC is over a canonical subset. Without an exact-field check a
  // caller could attach can_publish=true / can_run_paid_motion=true and keep
  // the original valid signature, then fool a naive downstream consumer.
  const expectedFields = [
    'plan_sha256', 'motion_sha256', 'shop_id', 'campaign_id',
    'reviewer_id', 'approved_at_utc', 'decision',
    'can_publish', 'can_run_paid_motion', 'hmac_sha256'
  ];
  if (!receipt || typeof receipt !== 'object' || Array.isArray(receipt) ||
      Object.keys(receipt).sort().join('|') !== expectedFields.sort().join('|') ||
      receipt.decision !== 'CREATIVE_ONLY_APPROVED_NOT_PUBLISHED' ||
      receipt.can_publish !== false || receipt.can_run_paid_motion !== false)
    reject('Editorial-only receipt fields must match exactly');
  if (creative.shop_id !== expectedShop ||
      receipt.plan_sha256 !== sha || receipt.motion_sha256 !== hash(bundle.motion_direction_v1) ||
      receipt.shop_id !== expectedShop ||
      receipt.campaign_id !== creative.campaign_id || !id(receipt.reviewer_id) ||
      !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/.test(receipt.approved_at_utc)) reject('Approval not bound to current shop/campaign');
  const stamp = Date.parse(receipt.approved_at_utc);
  if (!Number.isFinite(stamp) || stamp > Date.now() + 300000 ||
      stamp < Date.now() - 365 * 24 * 60 * 60 * 1000) reject('Stale or future approval receipt');
  const payload = payloadOf(receipt.plan_sha256, receipt.motion_sha256, receipt.shop_id, receipt.campaign_id,
    receipt.reviewer_id, receipt.approved_at_utc);
  const expected = Buffer.from(signatureOf(payload, secretKey), 'hex');
  const actual = typeof receipt.hmac_sha256 === 'string' && /^[a-f0-9]{64}$/.test(receipt.hmac_sha256)
    ? Buffer.from(receipt.hmac_sha256, 'hex') : Buffer.alloc(32);
  if (!crypto.timingSafeEqual(expected, actual)) reject('HMAC signature mismatch');
  return true;
}
// Server-only trusted adapter. These readers MUST be server-injected, not
// JSON, and must each use the original verified user's JWT and fresh current
// RLS rows. No HTTP endpoint or paid model dispatch is enabled by this helper.
function approveCreativeDraftFromTrustedReaders(bundle, authorization, shopId, readers, secretKey) {
  guardKey(secretKey);
  const creative = bundle?.creative_direction_v1;
  if (!creative || creative.shop_id !== shopId ||
      typeof authorization !== 'string' || !authorization.startsWith('Bearer ') ||
      !readers || typeof readers.verifyJwt !== 'function' ||
      typeof readers.currentMembership !== 'function' ||
      typeof readers.readEditorialReview !== 'function')
    reject('Trusted current JWT, membership and review sources required');
  const jwt = authorization.slice(7).trim();
  if (jwt.length < 8 || jwt.length > 16384) reject('Invalid current JWT');
  let actor, member, review;
  try {
    actor = readers.verifyJwt(jwt);
    if (!id(actor)) reject('Authenticated reviewer identifier required');
    member = readers.currentMembership(jwt, actor, shopId);
    if (!member || member.active !== true || member.shop_id !== shopId ||
        member.user_id !== actor || !['OWNER', 'EDITOR'].includes(member.role))
      reject('Current OWNER or EDITOR membership required');
    review = readers.readEditorialReview(jwt, actor, shopId, creative.campaign_id);
  } catch (error) {
    reject('Current JWT/RLS editorial review cannot be verified');
  }
  const originalPlanSha = expectedPlanSha(bundle);
  const motionSha = hash(bundle.motion_direction_v1);
  if (!review || review.shop_id !== shopId ||
      review.campaign_id !== creative.campaign_id ||
      review.reviewer_id !== actor || review.plan_sha256 !== originalPlanSha ||
      review.motion_sha256 !== motionSha || review.revoked_at != null ||
      review.source_media_current !== true ||
      review.claims_current !== true ||
      review.approved_by_human !== true)
    reject('Current source rights, human approval and complete plan hashes required');
  // Fresh membership after the read, so an editor revoked mid-request cannot sign.
  try {
    const next = readers.currentMembership(jwt, actor, shopId);
    if (!next || next.active !== true || next.shop_id !== shopId ||
        next.user_id !== actor || !['OWNER', 'EDITOR'].includes(next.role))
      reject('Current reviewer membership revoked before signing');
  } catch (error) {
    reject('Current reviewer membership cannot be revalidated');
  }
  const reviewer = {
    id: actor, shop_id: shopId, role: member.role,
    server_verified: true, current_member: true,
    completed_claims_review: true, completed_media_rights_review: true,
    completed_storyboard_review: true, completed_script_review: true
  };
  return approveCreativeDraft(bundle, reviewer, secretKey);
}
function editorHandoff(bundle, receipt, secretKey, expectedShop) {
  verifyCreativeApproval(bundle, receipt, secretKey, expectedShop);
  const plan = bundle.creative_direction_v1;
  // This source adapter does not actually call Feature4/Feature5 or charge.
  // Feature4 must authenticate its own request and F5 must separately inspect
  // approved provider profile + media grants + per-shop spend gate.
  return {
    contract: 'feature2_to_feature4_handoff_v1',
    shop_id: plan.shop_id, campaign_id: plan.campaign_id,
    duration_seconds: plan.duration_seconds, aspect_ratio: plan.aspect_ratio,
    creative_direction_v1: structuredClone(plan), motion_direction_v1: structuredClone(bundle.motion_direction_v1),
    editorial_receipt: structuredClone(receipt),
    feature3_media_must_be_revalidated: true,
    feature5_provider_and_cost_must_be_approved: true,
    can_publish: false, can_dispatch_paid_motion: false
  };
}
module.exports = { expectedPlanSha, approveCreativeDraft, approveCreativeDraftFromTrustedReaders,
  verifyCreativeApproval, editorHandoff };
