/** Opt-in, on-demand GPU job history. No signed-image links or GPU calls. */
import {useEffect, useRef, useState} from 'react'
import {scopedFeature3GeneratedHistory,validateFeature3GeneratedHistory} from './feature3-generated-history.mjs'

const initial = shopId => ({shopId,jobs:[],message:'',busy:false})
const STATUSES = {
  QUEUED:'Queued — output not generated',
  RUNNING:'Rendering — output not yet available',
  SUCCEEDED:'Generated privately — independent output review required',
  FAILED:'Failed — no output available',
}

export default function Feature3GeneratedHistory({shopId,api}) {
  const [state,setState]=useState(()=>initial(shopId))
  const epoch=useRef(0)
  const current=useRef({shopId,api})
  current.current={shopId,api}
  const checked=scopedFeature3GeneratedHistory(state,shopId)

  useEffect(()=>{
    setState(initial(shopId))
    return ()=>{epoch.current+=1}
  },[shopId,api])

  const load=async()=>{
    if(!api || !shopId || checked.busy)return
    const shop=shopId,source=api,nonce=++epoch.current
    const still=()=>nonce===epoch.current &&
      current.current.shopId===shop && current.current.api===source
    setState({...initial(shop),busy:true})
    try{
      // Existing JWT+RLS API only; no GPU POST and no download-token mint.
      const list=await source.listGeneratedJobs(shop)
      const jobs=validateFeature3GeneratedHistory(shop,list)
      if(still())setState({shopId:shop,jobs,
        busy:false,message:jobs.length
          ? 'These statuses are private; every image still requires independent review and authorization.'
          : 'No generated images recorded for this shop.'})
    }catch{
      if(still())setState({...initial(shop),
        message:'Private generated-image history unavailable or access revoked.'})
    }
  }
  return <section aria-label="Private generated-image job history">
    <div style={{display:'flex',alignItems:'center',gap:8,flexWrap:'wrap'}}>
      <button type="button" onClick={load} disabled={!api||!shopId||checked.busy}>
        {checked.busy?'Checking private jobs…':'Check my generated-image history'}
      </button>
      <small>Read-only. No GPU call, no public URL or automatic download.</small>
    </div>
    {checked.message&&<p role="status">{checked.message}</p>}
    {checked.jobs.length>0&&<ul aria-label="Private generated job statuses">
      {checked.jobs.map(job=><li key={job.id}>
        Job {job.id.slice(0,8)} — {STATUSES[job.status]}
      </li>)}
    </ul>}
  </section>
}
