'use strict';
const assert = require('node:assert/strict');
const { directorPrompt, compile, revisionTargets, revise } = require('../director');

function source(duration) {
  return {
    shop_id: 'shop-test-403', campaign_id: 'campaign-diwali-01', duration_seconds: duration,
    business_name: 'Thread and Loom Studio', campaign_date: '2026-11-06', authenticated_owner_or_editor: true, server_verified: true,
    creative_brief: 'Create an elegant Diwali kurti promotion showing authentic garment motion, no artificial extravagance.',
    target_audience: 'Adults buying festive Indian clothing for family celebrations',
    brand_voice: 'Warm, elegant and restrained premium boutique tone',
    advertising_objective: 'Explain the authorized 20 percent festive promotion and invite visits',
    approved_offers: [{
      id: 'sale-offer-20', shop_id: 'shop-test-403', approval_status: 'APPROVED',
      percent_off: 20, signed_evidence_id: 'approval-record-owner-20', active: true,
      eligible_product_skus: ['KURTI-RED-01'], approved_claim_text: '20% off selected kurtis',
      valid_from: '2026-10-01', valid_until: '2026-11-15'
    }],
    media_grants: [{
      id: 'asset-approved-red-kurti', shop_id: 'shop-test-403', kind: 'IMAGE',
      rights_status: 'APPROVED', product_sku: 'KURTI-RED-01',
      private: true, commercial_use_allowed: true, revoked_at: null,
      original_media_sha256: 'a'.repeat(64),
      garment_facts: {
        color: 'deep red', neckline: 'round neckline', sleeves: 'full-length sleeves',
        hem: 'straight knee-length hem', embroidery: 'gold motifs across the front'
      }
    }]
  };
}
function candidate(duration) {
  const count = duration / 5, scenes = [];
  for (let i = 0; i < count; i += 1) {
    const scene = i + 1, last = i === count - 1;
    const voiceover = last ? 'Celebrate Diwali with thoughtful festive style' :
      ('Discover festive styling detail number ' + scene + ' today');
    scenes.push({
      id: 's' + scene, role: i === 0 ? 'hook' : last ? 'cta' : i % 3 === 0 ? 'offer' : 'product',
      voiceover, dialogue: '',
      transition_out: last ? 'gentle fade into the approved end card' : 'clean editorial cut on motion',
      shots: [{
        id: 'shot-' + scene, duration_seconds: 5, reference_asset_id: 'asset-approved-red-kurti',
        product_sku: 'KURTI-RED-01',
        visual_description: 'Premium festive boutique editorial frame ' + scene +
          ' featuring an adult fashion model in an approved deep red kurti with real fabric textures and grounded movement.',
        subject: 'Adult model maintaining the approved reference pose and facial identity',
        character_continuity: 'One adult model with unchanged features, hair, silhouette and identity throughout every shot',
        wardrobe: 'Exactly the approved deep red kurti, round neckline, full-length sleeves, straight knee-length hem and gold motifs',
        camera: {
          framing: 'head-to-toe full-body vertical hero framing',
          lens: '50mm normal perspective portrait lens',
          composition: 'centered full garment with head, hands and hem safely inside a 9:16 frame',
          movement: 'slow physical dolly backward at constant speed with no focal change'
        },
        lighting: 'Warm diffuse Diwali boutique practicals balanced with soft key and gentle edge light',
        background: 'Tasteful indoor festive boutique with subdued hanging lamps and unobtrusive decor',
        motion_steps: [
          { start_seconds: 0, end_seconds: 1.5,
            human_action: 'Model starts in a comfortable standing pose with natural breathing',
            camera_action: 'Steady camera establishes centered medium-wide framing',
            fabric_response: 'Deep red fabric rests under gravity with accurate gold motifs' },
          { start_seconds: 1.5, end_seconds: 5,
            human_action: 'Model takes two natural steps and turns gently three quarters at the end',
            camera_action: 'Camera dollies backward smoothly keeping full outfit in frame',
            fabric_response: 'Deep red kurti hem sways slightly and settles with unchanged neckline and embroidery' }
        ],
        generation_prompt: 'Shot ' + scene + ': premium photoreal Diwali fashion advertisement. The same adult model wears the exact deep red kurti from the approved first-frame image, keeping round neckline, full-length sleeves, straight knee-length hem and gold motifs across the front unchanged. At first stand still; then walk forward two natural steps and turn softly three-quarters. The boutique light is warm and diffused; camera tracks backward on a 50mm lens and holds the complete garment in portrait frame. Preserve anatomy, cloth physics and stable fabric design. No overlays or invented logos.',
        negative_constraints: ['No garment color or embroidery changes', 'No extra limbs, hands or faces', 'No flicker, jump cuts, extra people or rendered text']
      }]
    });
  }
  const fullVO = scenes.map(s => s.voiceover).join(' ');
  return {
    concept: 'An elegant Diwali kurti showcase centered on modest, realistic garment movement',
    hook: 'The festive wardrobe story starts with one beautiful detail',
    voiceover_script: fullVO,
    cta: 'Explore the approved festive collection: 20% off selected kurtis',
    offer_ids_used: ['sale-offer-20'],
    scenes
  };
}
function reject(fn, message) { assert.throws(fn, /FEATURE2_CREATIVE_DIRECTION_INVALID/, message); }
for (const duration of [15, 30, 60]) {
  const input = source(duration), authored = candidate(duration);
  const prompt = directorPrompt(input);
  assert.equal(prompt.provider, 'existing_azure_gpt_4_1_mini_via_feature2_budget_gate');
  assert.equal(prompt.paid_call_made, false);
  assert.ok(prompt.user.includes('asset-approved-red-kurti'));
  assert.ok(prompt.user.includes('Create an elegant Diwali kurti promotion'));
  const result = compile(input, authored);
  const creative = result.creative_direction_v1;
  assert.equal(creative.duration_seconds, duration);
  assert.equal(creative.scenes.length, duration / 5);
  assert.equal(result.motion_direction_v1.length, duration / 5);
  assert.equal(creative.scenes.at(-1).start_seconds + creative.scenes.at(-1).duration_seconds, duration);
  assert.equal(creative.audio_sync.state, 'ESTIMATED_PENDING_REAL_SPEECH_ALIGNMENT');
  assert.equal(result.approval_record.can_publish, false);
  assert.equal(result.approval_record.can_run_paid_motion, false);
  assert.match(result.approval_record.plan_sha256, /^[a-f0-9]{64}$/);
  assert.deepEqual(creative.authorized_offer_ids, ['sale-offer-20']);
  assert.match(creative.approved_offer_evidence_sha256, /^[a-f0-9]{64}$/);
  assert.match(creative.approved_media_evidence_sha256, /^[a-f0-9]{64}$/);
  const unique = new Set();
  for (const shot of result.motion_direction_v1) {
    assert.equal(shot.contract, 'motion_direction_v1');
    assert.equal(shot.duration_seconds, 5);
    assert.equal(shot.reference_media_id, 'asset-approved-red-kurti');
    assert.equal(shot.requested_profile.inference_approved, false);
    assert.equal(shot.requested_profile.provider_profile_verified, false);
    assert.ok(shot.generation_prompt.length >= 180);
    assert.equal(shot.choreography[0].start_seconds, 0);
    assert.equal(shot.choreography.at(-1).end_seconds, 5);
    assert.equal(shot.garment_lock.color, 'deep red');
    unique.add(shot.generation_prompt);
  }
  assert.equal(unique.size, duration / 5);
}
{
  const req = source(30), base = candidate(30);
  const changed = structuredClone(base);
  changed.scenes[0].shots[0].camera.movement = 'gentle camera lift while remaining steady and preserving full garment';
  assert.deepEqual(revisionTargets(compile(req, base), { scenes: { s1: 'Lift the camera gently' } }).ids, ['s1']);
  const revised = revise(req, compile(req, base), changed, { scenes: { s1: 'Lift the camera gently' } });
  assert.deepEqual(revised.approval_record.revised_scene_ids, ['s1']);
  assert.equal(revised.approval_record.approved, false);
  assert.notEqual(revised.approval_record.plan_sha256, compile(req, base).approval_record.plan_sha256);
  const unauthorized = structuredClone(base);
  unauthorized.scenes[1].shots[0].lighting = 'Unapproved completely different lighting with harsh colored strobe';
  reject(() => revise(req, compile(req, base), unauthorized, { scenes: { s1: 'Only edit first scene' } }), 'Untargeted edits must be denied');
  reject(() => revisionTargets(compile(req, base), { scenes: { absent: 'Change it' } }), 'Nonexistent scene must be denied');
}
{
  const req = source(15), base = candidate(15);
  const foreign = structuredClone(req);
  foreign.media_grants[0].shop_id = 'another-shop';
  reject(() => compile(foreign, base), 'Cross-tenant media not allowed');
  const disabled = structuredClone(req);
  disabled.server_verified = false;
  reject(() => compile(disabled, base), 'Untrusted client cannot grant permissions');
  const modifiedOriginal = structuredClone(req);
  modifiedOriginal.media_grants[0].original_media_sha256 = 'b'.repeat(64);
  assert.notEqual(compile(modifiedOriginal, base).approval_record.plan_sha256, compile(req, base).approval_record.plan_sha256,
    'Changed original image bytes must change the creative approval digest');
  const broadenScope = structuredClone(req);
  broadenScope.approved_offers[0].eligible_product_skus.push('KURTI-BLUE-02');
  assert.notEqual(compile(broadenScope, base).approval_record.plan_sha256, compile(req, base).approval_record.plan_sha256,
    'Expanded sale SKU eligibility must invalidate the prior approved creative digest');
  const revokedOriginal = structuredClone(req);
  revokedOriginal.media_grants[0].revoked_at = '2026-11-01T10:00:00Z';
  reject(() => compile(revokedOriginal, base), 'Revoked private source cannot become premium video reference');
  const unlicensedOriginal = structuredClone(req);
  unlicensedOriginal.media_grants[0].commercial_use_allowed = false;
  reject(() => compile(unlicensedOriginal, base), 'Unlicensed first frame must be blocked');
  const outsideScope = structuredClone(req);
  outsideScope.approved_offers[0].eligible_product_skus = ['KURTI-BLUE-02'];
  reject(() => compile(outsideScope, base), 'A garment cannot inherit an unrelated SKU promotion');
  const noScope = structuredClone(req);
  delete noScope.approved_offers[0].eligible_product_skus;
  reject(() => compile(noScope, base), 'Unknown eligible SKU scope must fail closed');
  const forgedClaim = structuredClone(req);
  forgedClaim.approved_offers[0].approved_claim_text = '20% off all clothes';
  reject(() => compile(forgedClaim, base), 'Rewording promotion broader than approved claim fails');
  const mismatchedPercentage = structuredClone(req);
  mismatchedPercentage.approved_offers[0].approved_claim_text = '40% off selected kurtis';
  reject(() => compile(mismatchedPercentage, base), 'Legal claim must agree with documented percentage');
  const invalidCampaignDay = structuredClone(req);
  invalidCampaignDay.campaign_date = '2026-02-30';
  reject(() => compile(invalidCampaignDay, base), 'Invalid calendar date cannot authorize an offer');
  const invalidOfferDay = structuredClone(req);
  invalidOfferDay.approved_offers[0].valid_until = '2026-02-30';
  reject(() => compile(invalidOfferDay, base), 'Invalid expiry date cannot be approved');
  const expired = structuredClone(req);
  expired.approved_offers[0].valid_until = '2026-11-05';
  reject(() => compile(expired, base), 'No expired Diwali offer');
  const noOffer = structuredClone(req);
  noOffer.approved_offers = [];
  reject(() => compile(noOffer, base), '20% requires source approval');
  const lie = structuredClone(base);
  lie.cta = 'Explore the festive collection: 25% off selected kurtis';
  reject(() => compile(req, lie), 'Cannot invent offer');
  const wrongProduct = structuredClone(base);
  wrongProduct.scenes[0].shots[0].product_sku = 'FOREIGN';
  reject(() => compile(req, wrongProduct), 'Cannot swap garment');
  const bogusReference = structuredClone(base);
  bogusReference.scenes[0].shots[0].reference_asset_id = 'unregistered-client-image';
  reject(() => compile(req, bogusReference), 'Cannot forge reference');
  const brokenTime = structuredClone(base);
  brokenTime.scenes[0].shots[0].motion_steps[1].start_seconds = 2;
  reject(() => compile(req, brokenTime), 'No gaps in motion choreography');
  const tooShort = structuredClone(base);
  tooShort.scenes[0].shots[0].generation_prompt = 'A model moves';
  reject(() => compile(req, tooShort), 'No short generic prompts');
  const contradiction = structuredClone(base);
  contradiction.scenes[0].shots[0].generation_prompt = contradiction.scenes[0].shots[0].generation_prompt.replace('deep red', 'blue green');
  reject(() => compile(req, contradiction), 'No garment color changes');
  const unverified = structuredClone(base);
  unverified.scenes[0].shots[0].visual_description += ' Guaranteed best in India';
  reject(() => compile(req, unverified), 'No unsupported superiority');
  const absentNeckline = structuredClone(base);
  absentNeckline.scenes[0].shots[0].generation_prompt = absentNeckline.scenes[0].shots[0].generation_prompt.replace('round neckline', 'collar style');
  reject(() => compile(req, absentNeckline), 'Verified neckline cannot be removed from Feature5 prompt');
  const absentHem = structuredClone(base);
  absentHem.scenes[0].shots[0].generation_prompt = absentHem.scenes[0].shots[0].generation_prompt.replace('straight knee-length hem', 'floating hem');
  reject(() => compile(req, absentHem), 'Exact garment hem length cannot be invented');
  const absentEmbroider = structuredClone(base);
  absentEmbroider.scenes[0].shots[0].generation_prompt = absentEmbroider.scenes[0].shots[0].generation_prompt.replace('gold motifs across the front', 'gold thread');
  reject(() => compile(req, absentEmbroider), 'Embroidery identity must survive Wan prompt');
  const falseDialogue = structuredClone(base);
  falseDialogue.scenes[0].dialogue = 'Get an extra 40% off right now';
  reject(() => compile(req, falseDialogue), 'Unapproved discounts cannot hide in spoken dialogue');
  const spelledDiscount = structuredClone(base);
  // Fully written-out number words still need a human editorial review;
  // the numeric percent spelled as 'percent' is deterministic.
  spelledDiscount.scenes[0].dialogue = 'Get 40 percent off right now';
  reject(() => compile(req, spelledDiscount), 'Spelled-out percentage must be bound to approved offer');
  const unverifiedPrice = structuredClone(base);
  unverifiedPrice.scenes[0].dialogue = 'Available for ₹999 today';
  reject(() => compile(req, unverifiedPrice), 'Unverified retailer price cannot be invented');
  const unverifiedFabric = structuredClone(base);
  unverifiedFabric.scenes[0].shots[0].visual_description += ' This is pure cotton';
  reject(() => compile(req, unverifiedFabric), 'No unverified garment composition claim');
  const freeDelivery = structuredClone(base);
  freeDelivery.scenes[0].dialogue = 'Free delivery with any purchase';
  reject(() => compile(req, freeDelivery), 'Unapproved delivery guarantees rejected');
  const falseAction = structuredClone(base);
  falseAction.scenes[0].shots[0].motion_steps[0].human_action += ' with guaranteed best in India results';
  reject(() => compile(req, falseAction), 'Choreography must also be screened for unsupported claims');
  const unverifiedNegative = structuredClone(base);
  unverifiedNegative.scenes[0].shots[0].negative_constraints[0] += ' Get 75% off';
  reject(() => compile(req, unverifiedNegative), 'Even negative constraints cannot carry unapproved offer');
  const wordTimes = base.voiceover_script.split(/\s+/).map((text, i) => ({
    text, start: i * 0.15, end: (i + 1) * 0.15
  }));
  const alignment = { words: wordTimes, duration: wordTimes.length * 0.15 };
  const withWordTimes = compile(req, base, { actual_voice_alignment: alignment });
  assert.equal(withWordTimes.creative_direction_v1.audio_sync.state, 'WORD_TIMES_MATCH_PENDING_AUDIO_PROVENANCE');
  assert.equal(withWordTimes.approval_record.can_publish, false);
  const overlap = structuredClone(alignment);
  overlap.words[1].start = 0.01;
  reject(() => compile(req, base, { actual_voice_alignment: overlap }), 'Overlapping narrator timestamps must not pass');
  const outside = structuredClone(alignment);
  outside.words.at(-1).end = alignment.duration + 1;
  reject(() => compile(req, base, { actual_voice_alignment: outside }), 'Last word must not exceed actual audio duration');
  const voiceWrong = structuredClone(base);
  voiceWrong.voiceover_script = 'Audio does not match';
  reject(() => compile(req, voiceWrong), 'Narration must align');
  const missingEnd = structuredClone(base);
  missingEnd.scenes.pop();
  reject(() => compile(req, missingEnd), 'No timeline gaps');
  const misalignedAudio = { duration: 7, words: [{ text: 'madeup', start: 0, end: 1 }] };
  reject(() => compile(req, base, { actual_voice_alignment: misalignedAudio }), 'No fake speech alignment');
}
console.log('feature2 professional creative director: 15/30/60s, rich motion, source rights, claims, tempo and revision PASS');
