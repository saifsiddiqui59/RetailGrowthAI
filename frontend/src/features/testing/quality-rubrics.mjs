// Human-reviewed QA dimensions. These labels are not automated model scores,
// inference results, or authorization to publish, spend or reuse customer media.
export const QUALITY_RUBRICS = Object.freeze({
  F2: Object.freeze([
    {id:'overall',label:'Overall creative quality',next_check:'Review copy, brand tone, storyboard and verified claims.'},
    {id:'claim_accuracy',label:'Claim / offer accuracy',next_check:'Compare every product or discount claim to independently verified retailer source data.'},
    {id:'brand_voice',label:'Brand voice and language',next_check:'Revise captions and LinkedIn copy to match the approved business voice.'},
    {id:'storyboard',label:'Reel storyboard usefulness',next_check:'Check each shot, timing and CTA against the seven-day brief.'},
  ]),
  F3: Object.freeze([
    {id:'overall',label:'Overall poster quality',next_check:'Verify garment and model likeness, commercial rights and poster legibility.'},
    {id:'garment_identity',label:'Garment identity',next_check:'Compare garment shape, colors and pattern with the authorized original photo.'},
    {id:'human_anatomy',label:'Human anatomy',next_check:'Inspect model hands, faces, pose and garment/body interaction in the actual generated image.'},
    {id:'typography',label:'Poster text and layout',next_check:'Recheck message readability, safe claims and poster crop in the final deliverable.'},
  ]),
  F4: Object.freeze([
    {id:'overall',label:'Overall video composition',next_check:'Review pacing, approved media, caption legibility and mixed-audio quality.'},
    {id:'pacing',label:'Pacing and transitions',next_check:'Inspect shot lengths, transitions and 30-second narrative flow in the real MP4.'},
    {id:'captions',label:'Captions and subtitles',next_check:'Compare rendered captions with the approved script and on-screen contrast/safe area.'},
    {id:'audio',label:'Voiceover and music mix',next_check:'Listen for intelligible speech, music balance, clipping and synchronization.'},
  ]),
  F5: Object.freeze([
    {id:'overall',label:'Overall AI motion',next_check:'Review actual licensed motion output and temporal/garment identity fidelity.'},
    {id:'temporal_coherence',label:'Temporal coherence',next_check:'Inspect frame-to-frame flicker, subject drift and camera continuity.'},
    {id:'garment_continuity',label:'Garment continuity',next_check:'Compare product seams, logos and colors frame-by-frame to the approved garment.'},
    {id:'motion_artifacts',label:'Motion artifacts',next_check:'Check hands, limbs, occlusion and warped objects throughout the generated clip.'},
  ]),
  F7: Object.freeze([
    {id:'overall',label:'Overall editing',next_check:'Check cuts, timing, subtitles and rendered output against the source edit brief.'},
    {id:'cuts',label:'Cut selection and timing',next_check:'Compare cut points with the spoken story and actual source media rights.'},
    {id:'subtitles',label:'Subtitle accuracy',next_check:'Compare time-aligned subtitles with speech-to-text and real exported frames.'},
    {id:'sync',label:'Voice/music synchronization',next_check:'Review alignment between dialogue, music, scene changes and final audio peaks.'},
  ]),
})
export function dimensionsFor(feature) {
  return QUALITY_RUBRICS[feature] || []
}
export function acceptedDimension(feature, dimension) {
  const list=dimensionsFor(feature)
  return list.find(item=>item.id===dimension) || null
}
export function dimensionAdvice(feature, dimension) {
  return acceptedDimension(feature,dimension)?.next_check || null
}
