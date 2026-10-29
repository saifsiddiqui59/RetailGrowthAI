// Feature2 client-side VOICE SELECTOR model, never a billing/rights authority.
// Source names from Microsoft's published neural voice catalog.
// The actual Azure Speech region availability is verified by backend/runtime.
export const F2_VOICES = Object.freeze([
  {id:'en-IN-NeerjaNeural',locale:'en-IN',language:'Indian English',name:'Neerja',gender:'Female'},
  {id:'en-IN-PrabhatNeural',locale:'en-IN',language:'Indian English',name:'Prabhat',gender:'Male'},
  {id:'hi-IN-SwaraNeural',locale:'hi-IN',language:'Hindi',name:'Swara',gender:'Female'},
  {id:'hi-IN-MadhurNeural',locale:'hi-IN',language:'Hindi',name:'Madhur',gender:'Male'},
  {id:'mr-IN-AarohiNeural',locale:'mr-IN',language:'Marathi',name:'Aarohi',gender:'Female'},
  {id:'mr-IN-ManoharNeural',locale:'mr-IN',language:'Marathi',name:'Manohar',gender:'Male'},
])
export const VOICE_MODES = Object.freeze(['ai','uploaded','none'])
export const VOICE_SPEEDS = Object.freeze(['normal','slow','fast'])
const UUID=/^[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}$/
const SHA=/^[a-f0-9]{64}$/
const invalid=()=>{throw new Error('Invalid or unauthorized voiceover selection')}
export const voiceChoices = locale => F2_VOICES.filter(v=>v.locale===locale)
export const emptyVoiceSelection = () => ({
  mode:'none',language:null,voice_id:null,speed:'normal',audio_asset_id:null,
})
export function validateVoiceSelection(source,{shopId,approvedAudioAssets=[]}={}) {
  if(!source||typeof source!=='object'||Array.isArray(source)||
    Object.keys(source).sort().join('|')!=='audio_asset_id|language|mode|speed|voice_id'||
    typeof shopId!=='string'||!UUID.test(shopId)||!VOICE_MODES.includes(source.mode)||
    !VOICE_SPEEDS.includes(source.speed)||!Array.isArray(approvedAudioAssets))invalid()
  if(source.mode==='none'){
    if(source.audio_asset_id!==null||source.language!==null||
      source.voice_id!==null) invalid()
  }else if(source.mode==='ai'){
    const voice=F2_VOICES.find(v=>v.id===source.voice_id)
    if(!voice||source.language!==voice.locale||source.audio_asset_id!==null)invalid()
  }else{
    if(source.voice_id!==null||source.language!==null||
      typeof source.audio_asset_id!=='string'||!UUID.test(source.audio_asset_id))invalid()
    const matching=approvedAudioAssets.filter(asset=>
      asset?.id===source.audio_asset_id && asset?.shop_id===shopId &&
      asset?.kind==='audio' && asset?.authorized===true)
    if(matching.length!==1)invalid()
  }
  return {...source}
}
export function makeVoiceAction({
  selection,shopId,campaignId,planSha256,approvedAudioAssets=[],
  userConfirmedCharge=false,idempotencyKey,preview=false,
}){
  const validated=validateVoiceSelection(selection,{shopId,approvedAudioAssets})
  if(validated.mode!=='ai'||userConfirmedCharge!==true||
    typeof campaignId!=='string'||!UUID.test(campaignId)||
    typeof planSha256!=='string'||!SHA.test(planSha256)||
    typeof idempotencyKey!=='string'||!UUID.test(idempotencyKey)||
    typeof preview!=='boolean')invalid()
  // This object is solely a draft request. Server MUST fetch current exact
  // tenant plan, authorized actor + subscription, reserve cost and rights.
  return Object.freeze({
    shop_id:shopId,campaign_id:campaignId,
    creative_plan_sha256:planSha256,
    voice_id:validated.voice_id,
    language:validated.language,
    speed:validated.speed,
    preview,
    user_confirmed_charge:true,
    idempotency_key:idempotencyKey,
  })
}

/** Actual upstream 0.6.1 v1 English voices; different from Azure voices. */
export const F2_LOCAL_VOICES=Object.freeze([
 {id:'af_heart',locale:'en-us',name:'Heart',gender:'Female'},
 {id:'af_sarah',locale:'en-us',name:'Sarah',gender:'Female'},
 {id:'am_adam',locale:'en-us',name:'Adam',gender:'Male'},
 {id:'am_michael',locale:'en-us',name:'Michael',gender:'Male'},
 {id:'bf_emma',locale:'en-gb',name:'Emma',gender:'Female'},
 {id:'bf_isabella',locale:'en-gb',name:'Isabella',gender:'Female'},
 {id:'bm_george',locale:'en-gb',name:'George',gender:'Male'},
 {id:'bm_lewis',locale:'en-gb',name:'Lewis',gender:'Male'},
])
export function makeLocalVoiceAction({
 shopId,campaignId,planSha256,idempotencyKey,voiceId,lang,speed,preview=false,
}){
 if(!UUID.test(shopId)||!UUID.test(campaignId)||!UUID.test(idempotencyKey)||
    !SHA.test(planSha256)||!VOICE_SPEEDS.includes(speed)||typeof preview!=='boolean'||
    !F2_LOCAL_VOICES.some(v=>v.id===voiceId&&v.locale===lang))invalid()
 return Object.freeze({schema:'retailgrowth.feature2-local-voice-job.v1',
   shop_id:shopId,campaign_id:campaignId,creative_plan_sha256:planSha256,
   voice_id:voiceId,language:lang,speed,preview,
   provider:'kokoro-onnx',request_key:idempotencyKey,
   needs_current_server_signed_grants:true,
   may_auto_invoke_azure:false,estimated_paid_cost_usd:0})
}
