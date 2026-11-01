/** Opt-in, on-demand GPU job history. No signed-image links or GPU calls. */
import {useEffect, useRef, useState} from 'react'
import {
  scopedFeature3GeneratedHistory,validateFeature3GeneratedHistory,
  filteredFeature3GeneratedHistory,FEATURE3_HISTORY_FILTERS,
} from './feature3-generated-history.mjs'
import {createFeature3GeneratedBlobScope} from './feature3-generated-blob-scope.mjs'

const initial = (shopId, api = null) => ({shopId,api,jobs:[],message:'',busy:false})
const STATUSES = {
  QUEUED:'Queued — output not generated',
  RUNNING:'Rendering — output not yet available',
  SUCCEEDED:'Generated privately — independent output review required',
  FAILED:'Failed — no output available',
}

export default function Feature3GeneratedHistory({shopId,api,binaryClient=null}) {
  const [state,setState]=useState(()=>initial(shopId,api))
  const [image,setImage]=useState(null)
  const [imageBusy,setImageBusy]=useState(false)
  const [imageMessage,setImageMessage]=useState('')
  const [filter,setFilter]=useState('ALL')
  const epoch=useRef(0)
  // React state updates are asynchronous; guard a second Preview click before
  // imageBusy rerenders, without invalidating the first authorized request.
  const imageReadToken=useRef(null)
  // Prevent double history GETs before React commits checked.busy.
  const historyReadToken=useRef(null)
  const registry=useRef(null)
  if(!registry.current)registry.current=createFeature3GeneratedBlobScope()
  const current=useRef({shopId,api,binaryClient})
  current.current={shopId,api,binaryClient}
  const checked=scopedFeature3GeneratedHistory(state,shopId,api)
  const visibleJobs=checked.jobs.length
    ? filteredFeature3GeneratedHistory(shopId,checked.jobs,filter)
    : []
  const displayed=image?.shopId===shopId && image?.api===api &&
    image?.binaryClient===binaryClient &&
    visibleJobs.some(row=>row.id===image.jobId && row.status==='SUCCEEDED') &&
    registry.current.view(shopId,image.jobId)===image.url
    ? image : null
  useEffect(()=>{
    // A browser revoke failure must not interrupt the React privacy reset.
    // The scope registry keeps the hidden owned URL for a later retry.
    let cleanupPending=false
    imageReadToken.current=null
    historyReadToken.current=null
    try { registry.current.selectScope(shopId) }
    catch { cleanupPending=true }
    setState(initial(shopId,api))
    setImage(null)
    setImageBusy(false)
    setImageMessage(cleanupPending
      ? 'Private preview hidden; browser cleanup pending. Retry after recovery.'
      : '')
    setFilter('ALL')
    return ()=>{
      epoch.current+=1
      imageReadToken.current=null
      historyReadToken.current=null
      try { registry.current.clear() }
      catch { /* hidden pending URL stays in the private registry */ }
    }
  },[shopId,api,binaryClient])

  const load=async()=>{
    if(!api || !shopId || checked.busy || historyReadToken.current!==null)return
    const shop=shopId,source=api,nonce=++epoch.current
    imageReadToken.current=null
    setImage(null)
    setImageBusy(false)
    setImageMessage('')
    try { registry.current.clear() }
    catch {
      setImageMessage('Private preview hidden; browser cleanup pending. Retry after recovery.')
      return
    }
    const refreshToken=Symbol('private-generated-history')
    historyReadToken.current=refreshToken
    const still=()=>nonce===epoch.current &&
      current.current.shopId===shop && current.current.api===source
    setState({...initial(shop,source),busy:true})
    try{
      // Existing JWT+RLS API only; no GPU POST and no download-token mint.
      const list=await source.listGeneratedJobs(shop)
      const jobs=validateFeature3GeneratedHistory(shop,list)
      if(still())setState({shopId:shop,api:source,jobs,
        busy:false,message:jobs.length
          ? 'These statuses are private; every image still requires independent review and authorization.'
          : 'No generated images recorded for this shop.'})
    }catch{
      if(still())setState({...initial(shop,source),
        message:'Private generated-image history unavailable or access revoked.'})
    }finally{
      if(historyReadToken.current===refreshToken){
        historyReadToken.current=null
        // Clear/filter or a competing private preview can invalidate the
        // nonce before the GET settles. Never leave history permanently busy.
        if(!still())setState(previous=>
          previous.shopId===shop && previous.api===source && previous.busy
            ? {...previous,busy:false,message:'Private history refresh cancelled.'}
            : previous)
      }
    }
  }
  const loadImage=async(job)=>{
    if(!binaryClient || !api || !shopId || imageBusy || checked.busy ||
       historyReadToken.current!==null || imageReadToken.current!==null ||
       job?.status!=='SUCCEEDED' ||
       !checked.jobs.some(row=>row.id===job.id && row.status==='SUCCEEDED'))return
    const shop=shopId,source=binaryClient,historyApi=api,nonce=++epoch.current
    const readToken=Symbol('private-generated-preview')
    imageReadToken.current=readToken
    const still=()=>nonce===epoch.current &&
      current.current.shopId===shop && current.current.binaryClient===source &&
      current.current.api===historyApi
    setImage(null)
    setImageBusy(true)
    setImageMessage('')
    try{
      registry.current.clear()
      const verified=await source.get(shop,job.id)
      if(!still())return
      registry.current.selectScope(shop)
      const url=registry.current.install(shop,job.id,verified)
      if(!still()){registry.current.clear();return}
      setImage({shopId:shop,jobId:job.id,api:historyApi,binaryClient:source,url})
      setImageMessage('Unreviewed private preview — not approved for publication.')
    }catch{
      if(still())setImageMessage(
        'Private image unavailable or rights revoked. No preview was retained.')
    }finally{
      // A stale request must never unlock a newer in-flight private read.
      if(imageReadToken.current===readToken)imageReadToken.current=null
      if(still())setImageBusy(false)
    }
  }
  const clearImage=()=>{
    ++epoch.current
    imageReadToken.current=null
    setImage(null)
    setImageBusy(false)
    setImageMessage('')
    try { registry.current.clear() }
    catch {
      setImageMessage('Private preview hidden; browser cleanup pending. Retry Clear.')
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
    {checked.jobs.length>0&&<div style={{display:'flex',alignItems:'center',gap:8,flexWrap:'wrap'}}>
      <label>Show generated jobs
        <select aria-label="Filter private generated jobs by status"
          value={filter} disabled={checked.busy} onChange={event=>{
            // A filter switch invalidates in-flight preview fetches and
            // frees already decoded local private Blob pixels immediately.
            clearImage()
            setFilter(event.target.value)
          }}>
          {FEATURE3_HISTORY_FILTERS.map(status=><option key={status} value={status}>
            {status==='ALL'?'All statuses':status==='SUCCEEDED'
              ?'Generated — unreviewed':status.toLowerCase()}
          </option>)}
        </select>
      </label>
      <small>{visibleJobs.length} of {checked.jobs.length} private jobs shown</small>
    </div>}
    {checked.jobs.length>0&&visibleJobs.length===0&&
      <p role="status">No private jobs with this status.</p>}
    {visibleJobs.length>0&&<ul aria-label="Private generated job statuses">
      {visibleJobs.map(job=><li key={job.id}>
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
        style={{maxWidth:240,maxHeight:320,objectFit:'contain'}}
        onError={()=>{
          // A malformed but SHA-matching PNG may fail at the browser decoder.
          // Drop only this exact local URL; stale error events cannot clear
          // a newer image or another tenant's preview.
          if(registry.current.discardFailed(displayed.shopId,displayed.jobId,displayed.url)){
            ++epoch.current
            setImage(null)
            setImageBusy(false)
            setImageMessage('Private PNG preview could not be decoded. Local image was discarded.')
          }
        }}/>
      <figcaption>Private output requires independent review before reuse or publication.</figcaption>
      <button type="button" onClick={clearImage}>Clear private preview</button>
    </figure>}
  </section>
}
