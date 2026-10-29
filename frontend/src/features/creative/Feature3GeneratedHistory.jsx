/** Opt-in, on-demand GPU job history. No signed-image links or GPU calls. */
import {useEffect, useRef, useState} from 'react'
import {scopedFeature3GeneratedHistory,validateFeature3GeneratedHistory} from './feature3-generated-history.mjs'
import {createFeature3GeneratedBlobScope} from './feature3-generated-blob-scope.mjs'

const initial = shopId => ({shopId,jobs:[],message:'',busy:false})
const STATUSES = {
  QUEUED:'Queued — output not generated',
  RUNNING:'Rendering — output not yet available',
  SUCCEEDED:'Generated privately — independent output review required',
  FAILED:'Failed — no output available',
}

export default function Feature3GeneratedHistory({shopId,api,binaryClient=null}) {
  const [state,setState]=useState(()=>initial(shopId))
  const [image,setImage]=useState(null)
  const [imageBusy,setImageBusy]=useState(false)
  const [imageMessage,setImageMessage]=useState('')
  const epoch=useRef(0)
  const registry=useRef(null)
  if(!registry.current)registry.current=createFeature3GeneratedBlobScope()
  const current=useRef({shopId,api,binaryClient})
  current.current={shopId,api,binaryClient}
  const checked=scopedFeature3GeneratedHistory(state,shopId)
  const displayed=image?.shopId===shopId && image?.binaryClient===binaryClient &&
    checked.jobs.some(row=>row.id===image.jobId && row.status==='SUCCEEDED')
    ? image : null
  useEffect(()=>{
    registry.current.selectScope(shopId)
    setState(initial(shopId))
    setImage(null)
    setImageBusy(false)
    setImageMessage('')
    return ()=>{epoch.current+=1;registry.current.clear()}
  },[shopId,api,binaryClient])

  const load=async()=>{
    if(!api || !shopId || checked.busy)return
    const shop=shopId,source=api,nonce=++epoch.current
    registry.current.clear()
    setImage(null)
    setImageMessage('')
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
  const loadImage=async(job)=>{
    if(!binaryClient || !api || !shopId || imageBusy || checked.busy ||
       job?.status!=='SUCCEEDED' ||
       !checked.jobs.some(row=>row.id===job.id && row.status==='SUCCEEDED'))return
    const shop=shopId,source=binaryClient,nonce=++epoch.current
    const still=()=>nonce===epoch.current &&
      current.current.shopId===shop && current.current.binaryClient===source
    registry.current.clear()
    setImage(null)
    setImageBusy(true)
    setImageMessage('')
    try{
      const verified=await source.get(shop,job.id)
      if(!still())return
      registry.current.selectScope(shop)
      const url=registry.current.install(shop,job.id,verified)
      if(!still()){registry.current.clear();return}
      setImage({shopId:shop,jobId:job.id,binaryClient:source,url})
      setImageMessage('Unreviewed private preview — not approved for publication.')
    }catch{
      if(still())setImageMessage(
        'Private image unavailable or rights revoked. No preview was retained.')
    }finally{
      if(still())setImageBusy(false)
    }
  }
  const clearImage=()=>{
    ++epoch.current
    registry.current.clear()
    setImage(null)
    setImageBusy(false)
    setImageMessage('')
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
        {binaryClient && job.status==='SUCCEEDED' && <button type="button"
          disabled={imageBusy||checked.busy} onClick={()=>loadImage(job)}>
          {imageBusy?'Checking private image…':'Preview privately'}
        </button>}
      </li>)}
    </ul>}
    {imageMessage && <p role="status">{imageMessage}</p>}
    {displayed && <figure>
      <img src={displayed.url} alt="Unreviewed private generated poster preview"
        style={{maxWidth:240,maxHeight:320,objectFit:'contain'}}/>
      <figcaption>Private output requires independent review before reuse or publication.</figcaption>
      <button type="button" onClick={clearImage}>Clear private preview</button>
    </figure>}
  </section>
}
