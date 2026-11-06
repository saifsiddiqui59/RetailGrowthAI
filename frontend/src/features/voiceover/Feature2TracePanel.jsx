import {useEffect,useRef,useState} from 'react'
import {verifyPrivateFeature2Trace} from './voiceover-trace-model.mjs'

// Source-only view: coordinator must supply a trusted authenticated RLS-backed
// private trace endpoint, NOT a browser-held HMAC secret or a fixture response.
export default function Feature2TracePanel({
  shopId,campaignId,workflowId,sourceSha256,
  enabled=false,onFetchPrivateTrace=null,
}){
  const [result,setResult]=useState(null)
  const [error,setError]=useState('')
  const [busy,setBusy]=useState(false)
  const current=shopId+':'+campaignId+':'+workflowId+':'+sourceSha256
  const scope=useRef(current)
  scope.current=current
  useEffect(()=>{
    setResult(null);setError('')
  },[current])
  async function refresh(){
    if(enabled!==true||typeof onFetchPrivateTrace!=='function'){
      setError('Authenticated private trace reader unavailable');return
    }
    const old=scope.current
    setError('');setBusy(true)
    try{
      const receipt=await onFetchPrivateTrace({
        shop_id:shopId,campaign_id:campaignId,
        workflow_id:workflowId,source_sha256:sourceSha256,
      })
      const clean=verifyPrivateFeature2Trace({
        shopId,campaignId,workflowId,sourceSha256,receipt,
      })
      if(old!==scope.current)throw Error('Campaign or workflow revoked during read')
      setResult(clean)
    }catch(e){
      setResult(null)
      setError(e?.message||'Current private trace could not be verified')
    }finally{setBusy(false)}
  }
  if(!workflowId||!sourceSha256)return null
  return <section aria-label="Private creative workflow trace">
    <h4>Feature-by-feature workflow status</h4>
    <p>Private backend stage evidence only. Source and synthetic tests are not actual
      speech, human approval, GPU video, or published Reels.</p>
    <button type="button" onClick={refresh}
      disabled={busy||!enabled||!onFetchPrivateTrace}>
      Read current protected workflow trace
    </button>
    {result&&<>
      <ol aria-label="Verified private workflow stages">
        {result.steps.map(step=><li key={step.sequence}>
          {step.stage}: {step.status} — {step.evidence_class}
          {step.failure_code?' ('+step.failure_code+')':''}
        </li>)}
      </ol>
      <p>Stage completion is not media quality approval, verified speech
        or customer publishing permission. Human and licensing reviews remain required.</p>
    </>}
    {error&&<p role="alert">{error}</p>}
  </section>
}
