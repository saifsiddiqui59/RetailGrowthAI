import {useEffect,useRef,useState} from 'react'
import {verifyPrivateFeature2Trace} from './voiceover-trace-model.mjs'
import {createPrivateTraceRequestGate} from './voiceover-trace-request-gate.mjs'

// Source-only view: coordinator must supply a trusted authenticated RLS-backed
// private trace endpoint, NOT a browser-held HMAC secret or a fixture response.
export default function Feature2TracePanel({
  shopId,campaignId,workflowId,sourceSha256,
  enabled=false,onFetchPrivateTrace=null,
}){
  const [result,setResult]=useState(null)
  const [error,setError]=useState('')
  const [busy,setBusy]=useState(false)
  const current=[shopId,campaignId,workflowId,sourceSha256,enabled===true].join(':')
  const gate=useRef(null)
  if(!gate.current)gate.current=createPrivateTraceRequestGate()
  gate.current.setScope(current)
  const readerRef=useRef(onFetchPrivateTrace)
  readerRef.current=onFetchPrivateTrace
  useEffect(()=>{
    gate.current.invalidate()
    setResult(null);setError('');setBusy(false)
  },[current,onFetchPrivateTrace])
  async function refresh(){
    if(enabled!==true||typeof onFetchPrivateTrace!=='function'){
      setError('Authenticated private trace reader unavailable');return
    }
    const ticket=gate.current.begin(current)
    const reader=onFetchPrivateTrace
    const stillCurrent=()=>gate.current.valid(ticket,current) && reader===readerRef.current
    setError('');setBusy(true)
    try{
      const receipt=await onFetchPrivateTrace({
        shop_id:shopId,campaign_id:campaignId,
        workflow_id:workflowId,source_sha256:sourceSha256,
      })
      const clean=verifyPrivateFeature2Trace({
        shopId,campaignId,workflowId,sourceSha256,receipt,
      })
      if(!stillCurrent())return
      setResult(clean)
    }catch(e){
      if(stillCurrent()){
        setResult(null)
        setError(e?.message||'Current private trace could not be verified')
      }
    }finally{if(stillCurrent())setBusy(false)}
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
