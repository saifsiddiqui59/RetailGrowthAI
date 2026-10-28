'use strict';
// This fixture is fully original, hand-authored synthetic test copy, NOT a real
// licensed garment, real 20%-off promotion or Azure model completion.
// It is intentionally rich enough to exercise the pinned MIT director
// storyboard, timing, motion choreography and source-approval compiler.
const SKU = 'KURTI-RED-01';
const GARMENT = Object.freeze({
  color: 'deep red',
  neckline: 'round neckline',
  sleeves: 'full-length sleeves',
  hem: 'straight knee-length hem',
  embroidery: 'gold motifs across the front',
});
const SCENES = [
  ['hook', 'Diwali begins with a quiet detail.',
    'full-body wide portrait at the doorway', 'slow gentle dolly inward',
    'Festive boutique doorway with distant diyas',
    'The adult model gently raises her chin to greet the warm doorway light',
    'The kurti rests then the lower fabric settles naturally'],
  ['product', 'Every motif tells a festive story.',
    'medium portrait framing at torso level', 'controlled lateral slide to the left',
    'A warmly lit boutique display with understated gold decor',
    'The model lifts one forearm to reveal the approved front embroidery',
    'The embroidery remains locked while the sleeve falls under gravity'],
  ['story', 'A soft silhouette moves with you.',
    'full garment front three-quarter portrait', 'smooth backward tracking dolly',
    'Textured indoor hallway with amber festive lights',
    'The model takes a careful measured step then gently turns toward camera',
    'The straight knee-length hem moves and settles without stretching'],
  ['product', 'Notice the shape, not the noise.',
    'medium head-to-waist vertical framing', 'subtle tripod tilt following hand movement',
    'Neutral boutique dressing area with soft practical lamps',
    'The model touches her own sleeve edge once and lowers her hand',
    'Full-length sleeve seam remains intact and follows the arm naturally'],
  ['benefit', 'Made for moments worth remembering.',
    'full-body clean vertical editorial portrait', 'slow tripod pan toward window light',
    'Quiet open boutique interior with gentle festive shadows',
    'The model pauses with a relaxed posture and shifts weight slowly',
    'Fabric drapes with believable mass and unchanged embroidery'],
  ['story', 'Warm light, thoughtful festive styling.',
    'medium-wide full-garment portrait', 'measured half-step side dolly',
    'Soft amber lantern backdrop without printed product text',
    'The model rotates her shoulders slightly toward the warm practicals',
    'The garment follows the rotation without changing neckline'],
  ['product', 'See the embroidery in natural light.',
    'mid portrait showing garment front', 'gentle vertical gimbal rise',
    'Cream boutique wall lit by an indirect window source',
    'The model opens her arms a little to reveal the embroidered panel',
    'Gold motifs stay aligned across front while sleeves drape'],
  ['story', 'The little pauses reveal more.',
    'full garment three-quarter silhouette', 'gradual steady forward push',
    'Uncluttered festive indoor corridor with gold bokeh',
    'The model stops and turns her head while keeping feet planted',
    'Hem settles after subtle torso movement with real fabric gravity'],
  ['benefit', 'Choose color that feels like celebration.',
    'wide full-length vertical framing', 'locked-off camera with careful rack focus',
    'Soft neutral backdrop and two distant golden lamps',
    'The model takes one gentle side step and rests naturally',
    'Deep red tone stays stable through lighting changes and body movement'],
  ['product', 'Take another look at the details.',
    'medium three-quarter editorial crop', 'short subtle sliding camera movement',
    'Simple boutique window display with quiet reflections',
    'The model adjusts her wrist position without obscuring the neckline',
    'Long sleeves move normally and embroidery never morphs'],
  ['story', 'A festive look, simply presented.',
    'full garment hero portrait', 'smooth short backward dolly',
    'Warm boutique entrance with restrained Diwali garlands',
    'The model takes a final small step and faces the camera calmly',
    'The straight hem sways and settles while motif geometry stays exact'],
  ['cta', 'Explore 20% off selected kurtis.',
    'wide full-length portrait with clean lower title-safe region', 'locked steady tripod camera',
    'Elegant neutral boutique wall ready for a later editor-generated sale card',
    'The model holds a natural confident standing pose and gently exhales',
    'The garment rests under gravity without pattern or silhouette changes'],
];
function verifiedBrief(durationSeconds=30) {
  if (![15,30,60].includes(durationSeconds)) throw new Error('Unsupported fixture duration');
  return {
    shop_id:'test-shop-403',campaign_id:'diwali-test-2026',
    duration_seconds:durationSeconds,campaign_date:'2026-11-06',
    business_name:'Thread and Loom Studio',
    creative_brief:'Create a premium Diwali fashion Reel showing only the approved real kurti with subtle lifelike adult-model motion.',
    target_audience:'Adults looking for understated festive Indian clothing',
    brand_voice:'Natural, elegant, restrained and genuinely warm boutique storytelling',
    advertising_objective:'Show actual approved kurti details and the precisely approved Diwali promotion',
    authenticated_owner_or_editor:true, server_verified:true,
    approved_offers:[{
      id:'test-approved-20',shop_id:'test-shop-403',approval_status:'APPROVED',active:true,
      percent_off:20,signed_evidence_id:'mock-signed-offer-source-only',
      eligible_product_skus:[SKU], approved_claim_text:'20% off selected kurtis',
      valid_from:'2026-10-01',valid_until:'2026-11-15',
    }],
    media_grants:[{
      id:'approved-first-frame-test', shop_id:'test-shop-403', kind:'IMAGE',
      rights_status:'APPROVED',private:true,commercial_use_allowed:true,revoked_at:null,
      original_media_sha256:'a'.repeat(64),product_sku:SKU,
      garment_facts:{...GARMENT},
    }]
  };
}
function authoredCandidate(durationSeconds=30) {
  if (![15,30,60].includes(durationSeconds)) throw new Error('Unsupported fixture duration');
  const total=durationSeconds/5;
  const selected=SCENES.slice(0,total).map((x)=>x.slice());
  // The last scene owns the exact CTA for each allowed duration.
  selected[total-1][0]='cta';
  selected[total-1][1]='Explore 20% off selected kurtis.';
  const scenes=selected.map(([role,voiceover,framing,movement,background,action,fabric],i)=>{
    const camera={framing, lens: i%2?'50mm normal portrait lens':'65mm natural portrait lens',
      composition:'Keep one adult model and the approved garment in stable 9:16 composition with no cut-off limbs',
      movement};
    const prompt=[
      'Shot '+(i+1)+' of '+total+': natural cinematic Indian Diwali fashion boutique, genuine first-frame image conditioning.',
      'The exact deep red garment has round neckline, full-length sleeves, straight knee-length hem and gold motifs across the front.',
      'Maintain the same adult face, hair, body dimensions, posture and single person across every shot.',
      'Begin with stable breathing: '+action+'.',
      'Then preserve authentic fabric physics: '+fabric+'.',
      'Camera: '+framing+' on '+camera.lens+', '+movement+'.',
      'Environment: '+background+'. Warm diffuse key and steady practical ambient lamps, believable light on cloth.',
      'Preserve source garment silhouette, sewing details, geometry, motif placement and dye color; no extra humans, logo or generated sale text.'
    ].join(' ');
    return {
      id:'scene-'+(i+1),role,voiceover,dialogue:'',
      transition_out:i===total-1?'soft fade to editor-controlled CTA title-safe area':'clean editorial cut respecting movement continuity',
      shots:[{
        id:'shot-'+(i+1),duration_seconds:5,reference_asset_id:'approved-first-frame-test',product_sku:SKU,
        visual_description:'Cinematic shot '+(i+1)+': '+framing+' with '+background+
          ' and meaningful single-model action while preserving the exact approved kurti with visible source-level fabric fidelity.',
        subject:'One approved adult fashion-model reference, unmodified face and silhouette',
        character_continuity:'One consistent adult model keeps the exact same facial identity, hairstyle, hands and body proportions',
        wardrobe:'Exactly the approved deep red kurti with round neckline, full-length sleeves, straight knee-length hem and gold motifs across the front',
        camera,
        lighting:'Soft warm diffused boutique key light with credible shadow direction and stable gold practicals',
        background,
        motion_steps:[
          {start_seconds:0,end_seconds:1.5,
            human_action:'The adult model prepares with natural breathing while remaining anatomically steady',
            camera_action:'Camera establishes '+framing+' using a physically stable tripod or dolly',
            fabric_response:'Approved kurti remains deep red with verified embroidery fixed in place'},
          {start_seconds:1.5,end_seconds:5,
            human_action:action,
            camera_action:'Camera executes '+movement+' while preserving the adult full garment proportions',
            fabric_response:fabric},
        ],
        generation_prompt:prompt,
        negative_constraints:[
          'Never change the deep red dye, seam lines or original gold front embroidery',
          'Never add an extra face, limb, person, watermark or AI-written text',
          'Never redesign round neckline, full-length sleeves or straight knee-length hem'
        ]
      }]
    };
  });
  return {
    concept:'A quiet, cinematic Diwali wardrobe story built on authentic kurti detail and lifelike movement',
    hook:'Festive elegance can start with a single detail.',
    voiceover_script:scenes.map(s=>s.voiceover).join(' '),
    cta:'Discover festive style: 20% off selected kurtis',
    offer_ids_used:['test-approved-20'],
    scenes
  };
}
module.exports={verifiedBrief,authoredCandidate,GARMENT,SCENES};
