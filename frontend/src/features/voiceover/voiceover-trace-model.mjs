// Private trace readback, intended for an authenticated, RLS-backed backend.
// This browser model NEVER validates server HMAC (secret cannot enter JS).
// A server-returned SOURCE_ONLY or synthetic test must not be shown as an
// executed / customer-publishable model, render or social result.
const SHA=/^[0-9a-f]{64}$/
const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/
const stages=new Set([
 "TREND","RETAILER_CONTEXT","AI_WRITER","PROMPT_IMPROVER",
 "SCRIPT_REVIEW","STORYBOARD","F3_MEDIA","KOKORO_TTS",
 "F7_TRANSCRIPTION","PRONUNCIATION_REVIEW","F4_EDITOR",
 "F5_MOTION","RENDER_HANDOFF",
])
const codes=new Set([
 "SOURCE_UNAVAILABLE","AUTH_DENIED","MEDIA_RIGHTS_REVOKED",
 "MODEL_UNAVAILABLE","UNSUPPORTED_PROVIDER","INVALID_INPUT",
 "WORKER_FAILED","BUDGET_BLOCKED","REVIEW_REQUIRED",
 "CONTRACT_MISMATCH","HANDOFF_PENDING","UNKNOWN",
])
const fail=()=>{throw Error("Trusted current private workflow trace unavailable")}
export function verifyPrivateFeature2Trace({
  shopId,campaignId,workflowId,sourceSha256,receipt
}={}){
  if(!UUID.test(shopId||"")||!UUID.test(campaignId||"")||
     !UUID.test(workflowId||"")||!SHA.test(sourceSha256||"")||
     !receipt||typeof receipt!=="object"||Array.isArray(receipt)||
     receipt.schema!=="retailgrowth.feature2-private-trace-history.v1"||
     receipt.shop_id!==shopId||receipt.campaign_id!==campaignId||
     receipt.workflow_id!==workflowId||receipt.source_sha256!==sourceSha256||
     receipt.private!==true||receipt.can_publish!==false||
     receipt.all_steps_verified!==true||
     receipt.actual_model_inference_verified!==false||
     !Array.isArray(receipt.events)||!receipt.events.length||
     receipt.events.length>100||
     !SHA.test(receipt.last_event_sha256||""))fail()
  let last=null
  const safe=receipt.events.map((e,i)=>{
    if(!e||typeof e!=="object"||Array.isArray(e)||
       Object.keys(e).sort().join("|")!==
         "can_publish|event_sha256|evidence_class|failure_code|sequence|stage|status"||
       e.sequence!==i+1||!stages.has(e.stage)||
       !["STARTED","SUCCEEDED","FAILED","BLOCKED"].includes(e.status)||
       !["SOURCE_ONLY","SYNTHETIC_TEST_ONLY","SIGNED_EXTERNAL"].includes(e.evidence_class)||
       !SHA.test(e.event_sha256||"")||
       e.can_publish!==false||
       (["FAILED","BLOCKED"].includes(e.status)?
        !codes.has(e.failure_code):e.failure_code!==null))fail()
    last=e.event_sha256
    return Object.freeze({
      sequence:e.sequence,stage:e.stage,status:e.status,
      evidence_class:e.evidence_class,failure_code:e.failure_code,
      // Even a signed external receipt only means the backend reported
      // independent evidence, not user editorial approval or real inference.
      customer_render_approved:false,
    })
  })
  if(last!==receipt.last_event_sha256)fail()
  return Object.freeze({
    status:"PRIVATE_BACKEND_STATUS_ONLY",
    steps:Object.freeze(safe),
    source_only_or_synthetic:safe.some(e=>
      e.evidence_class!=="SIGNED_EXTERNAL"),
    all_model_inference_verified:false,
    human_approval_verified:false,
    can_publish:false,
  })
}


// Bind a read-only private trace response to the EXACT UI reader/selection
// captured at request time. The callback identity must be replaced by the
// host whenever the current authenticated session/provider is replaced.
export function verifyCurrentPrivateTraceRead({
  currentScope,requestScope,receipt
}={}){
  if(!currentScope||typeof currentScope!=='object'||
     currentScope!==requestScope||
     currentScope.enabled!==true||
     typeof currentScope.onFetchPrivateTrace!=='function')fail()
  return verifyPrivateFeature2Trace({
    shopId:currentScope.shopId,campaignId:currentScope.campaignId,
    workflowId:currentScope.workflowId,
    sourceSha256:currentScope.sourceSha256,receipt,
  })
}
