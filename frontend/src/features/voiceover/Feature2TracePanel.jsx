import {useMemo,useRef,useState} from 'react'
import {verifyCurrentPrivateTraceRead} from './voiceover-trace-model.mjs'

// Only a trusted JWT/RLS-backed backend verifies worker HMAC. The browser
// keeps each verified projection tied to the *exact current* signed reader.
// A new authenticated session must install a new reader callback identity.
export default function Feature2TracePanel({
  shopId,campaignId,workflowId,sourceSha256,
  enabled=false,onFetchPrivateTrace=null,
}){
  // Object identity deliberately changes on tenant, workflow, role toggle
  // or backend provider replacement; avoid delimiter-collision string keys.
  const scope=useMemo(()=>Object.freeze({
    shopId,campaignId,workflowId,sourceSha256,
    enabled,onFetchPrivateTrace,
  }),[shopId,campaignId,workflowId,sourceSha256,enabled,onFetchPrivateTrace])
  const scopeRef=useRef(scope)
  scopeRef.current=scope
  const [snapshot,setSnapshot]=useState(null)
  const [alert,setAlert]=useState(null)
  const [busyScope,setBusyScope]=useState(null)
  const result=snapshot?.scope===scope&&enabled===true?snapshot.value:null
  const error=alert?.scope===scope?alert.value:''
  const busy=busyScope===scope
  async function refresh(){
    const requested=scopeRef.current
    if(requested.enabled!==true||typeof requested.onFetchPrivateTrace!=='function'){
      setAlert({scope:requested,value:'Authenticated private trace reader unavailable'})
      return
    }
    setAlert(null);setBusyScope(requested)
    try{
      const receipt=await requested.onFetchPrivateTrace({
        shop_id:requested.shopId,campaign_id:requested.campaignId,
        workflow_id:requested.workflowId,source_sha256:requested.sourceSha256,
      })
      // If shop/provider changed mid-read, never overwrite its UI with the old
      // receipt, or use the old callback's success to infer current access.
      if(requested!==scopeRef.current)return
      const clean=verifyCurrentPrivateTraceRead({
        currentScope:scopeRef.current,requestScope:requested,receipt,
      })
      setSnapshot({scope:requested,value:clean})
    }catch(e){
      if(requested===scopeRef.current){
        setSnapshot(null)
        setAlert({scope:requested,
          value:e?.message||'Current private trace could not be verified'})
      }
    }finally{
      if(requested===scopeRef.current)setBusyScope(null)
    }
  }
  if(!workflowId||!sourceSha256)return null
  return <section aria-label="Private creative workflow trace">
    <h4>Feature-by-feature workflow status</h4>
    <p>Private backend stage evidence only. Source and synthetic tests are not actual
      speech, human approval, GPU video, or published Reels.</p>
    <button type="button" onClick={refresh}
      disabled={busy||enabled!==true||typeof onFetchPrivateTrace!=='function'}>
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
