/** Optional, authenticated v2 drafts wrapper. Isolated from v1 saved posters.
 * Source-only: requires coordinator to supply feature3Api + registered private images.
 * No blind POST retries, no browser status promotion and no signed PNG claims.
 */
import { useEffect, useRef, useState } from 'react'
import Feature3StudioPanel from './Feature3StudioPanel.jsx'
import { validateFeature3Design } from './feature3-design.mjs'
import {scopedFeature3GeneratedLink,SAFE_CLIENT_LIFETIME_MS} from './feature3-signed-link-scope.mjs'
import { feature3ContextKey } from './feature3-context.mjs'
import {scopedFeature3WorkspaceValue,currentFeature3WorkspaceRequest} from './feature3-workspace-scope.mjs'

export default function Feature3SecureDraftWorkspace({
  shopId, campaignId, dayId, brandKit, imageMap = {}, approvedModels = [],
  approvedContent = null, feature3Api, disabled = false,
}) {
  const scopeKey=feature3ContextKey({shopId,campaignId,dayId})
  const [savedState,setSavedState] = useState({scope:scopeKey,value:[]})
  const [reopenedState,setReopenedState] = useState({scope:scopeKey,value:null})
  const [messageState,setMessageState] = useState({scope:scopeKey,value:''})
  const [busyState,setBusyState] = useState({scope:scopeKey,value:false})
  const [generatedState,setGeneratedState] = useState({scope:scopeKey,value:[]})
  const [generatedLink,setGeneratedLink] = useState(null)
  // Scope at render time, not only in a later useEffect cleanup: no stale
  // private job/draft/revision can appear on the first paint of a new shop/day.
  const saved=scopedFeature3WorkspaceValue(savedState,scopeKey,[])
  const reopened=scopedFeature3WorkspaceValue(reopenedState,scopeKey,null)
  const message=scopedFeature3WorkspaceValue(messageState,scopeKey,'')
  const busy=scopedFeature3WorkspaceValue(busyState,scopeKey,false)
  const generatedJobs=scopedFeature3WorkspaceValue(generatedState,scopeKey,[])
  const setMessage=value=>setMessageState({scope:scopeKey,value})
  const setBusy=value=>setBusyState({scope:scopeKey,value})
  const activeScope=useRef({shopId,scopeKey,feature3Api})
  activeScope.current={shopId,scopeKey,feature3Api}
  const pendingDownload=useRef(0)
  const pendingHistory=useRef(0)
  const pendingJobs=useRef(0)
  const ticket=useRef({scope:scopeKey,designId:null,revision:0})
  const pending=useRef({scope:scopeKey,active:false})
  const currentScope=(scope,provider)=>
    activeScope.current.scopeKey===scope && activeScope.current.feature3Api===provider
  const visibleGeneratedLink=!disabled ? scopedFeature3GeneratedLink(
    generatedLink,shopId,Date.now(),scopeKey) : null
  useEffect(()=>{
    pendingDownload.current+=1
    pendingHistory.current+=1
    pendingJobs.current+=1
    ticket.current={scope:scopeKey,designId:null,revision:0}
    pending.current={scope:scopeKey,active:false}
    setGeneratedLink(null)
    setSavedState({scope:scopeKey,value:[]})
    setReopenedState({scope:scopeKey,value:null})
    setGeneratedState({scope:scopeKey,value:[]})
    setMessageState({scope:scopeKey,value:''})
    setBusyState({scope:scopeKey,value:false})
  },[scopeKey,feature3Api])
  useEffect(()=>{
    if(!generatedLink)return
    const timer=setTimeout(()=>setGeneratedLink(null),SAFE_CLIENT_LIFETIME_MS)
    return ()=>clearTimeout(timer)
  },[generatedLink])

  const loadHistory = async () => {
    if (disabled || busy || (pending.current.scope===scopeKey && pending.current.active)) return
    const scope=scopeKey,provider=feature3Api,attempt=++pendingHistory.current
    const current=()=>currentFeature3WorkspaceRequest(
      activeScope.current,scope,provider,attempt,pendingHistory.current)
    setBusy(true);setMessage('')
    try {
      const rows=await feature3Api.listDesigns(shopId, campaignId, dayId)
      if(!current())return
      setSavedState({scope,value:rows})
      setMessage(rows.length ? 'Private draft history loaded.' :
        'No v2 private poster drafts exist for this day.')
    } catch {
      if(current())setMessage('Could not read this day’s authorized v2 draft history.')
    } finally {
      if(current())setBusy(false)
    }
  }

  const loadGenerated = async () => {
    if (disabled || busy || (pending.current.scope===scopeKey && pending.current.active)) return
    const scope=scopeKey,provider=feature3Api,attempt=++pendingJobs.current
    const current=()=>currentFeature3WorkspaceRequest(
      activeScope.current,scope,provider,attempt,pendingJobs.current)
    setBusy(true);setGeneratedLink(null);setMessage('')
    try {
      const jobs=await feature3Api.listGeneratedJobs(shopId)
      if(!current())return
      setGeneratedState({scope,value:jobs})
      setMessage(jobs.length ? 'Private generated image job history loaded.' :
        'No generated image jobs for this retailer.')
    } catch {
      if(current()){
        setGeneratedState({scope,value:[]})
        setMessage('Generated image history is unavailable or access was revoked.')
      }
    } finally { if(current())setBusy(false) }
  }

  const openGenerated = async jobId => {
    if (disabled || busy || (pending.current.scope===scopeKey && pending.current.active)) return
    const scope=shopId, provider=feature3Api, requestKey=scopeKey
    const attempt=++pendingDownload.current
    const current=()=>attempt===pendingDownload.current &&
      activeScope.current.shopId===scope &&
      activeScope.current.scopeKey===requestKey &&
      activeScope.current.feature3Api===provider
    setBusy(true); setGeneratedLink(null); setMessage('')
    try {
      const receipt = await provider.getGeneratedImageDownload(scope,jobId)
      if(!current())return
      setGeneratedLink({...receipt,scope,requestKey,createdAt:Date.now()})
      setMessage('Private link expires in 60 seconds. Image remains unreviewed.')
    } catch {
      if(current())setMessage('Private image unavailable, expired or no longer authorized.')
    } finally {
      if(current())setBusy(false)
    }
  }

  const restore = event => {
    const chosen = saved.find(d => d.id === event.target.value)
    if (!chosen) return
    try {
      if (chosen.status !== 'DRAFT') throw Error('Only editable drafts reopen')
      if (chosen.shop_id!==shopId || chosen.campaign_id!==campaignId ||
          chosen.day_id!==dayId) throw Error('Private draft context changed')
      const design = validateFeature3Design(chosen.design)
      if (design.shop_id !== shopId ||
          design.layers.some(layer => layer.type === 'image' &&
            (!imageMap[layer.asset_id]?.complete ||
             !imageMap[layer.asset_id]?.naturalWidth ||
             !imageMap[layer.asset_id]?.naturalHeight))) {
        throw Error('Shop media grant must be refreshed first')
      }
      ticket.current = {scope:scopeKey,designId:chosen.id,revision:chosen.revision}
      setReopenedState({scope:scopeKey,value:{
        id:chosen.id,revision:chosen.revision,design}})
      setMessage('Authorized editable draft reopened. Saving uses revision CAS.')
    } catch {
      setMessage('Draft is no longer editable or private media access changed.')
    }
  }

  const saveDesign = async design => {
    const scope=scopeKey,provider=feature3Api
    if (disabled || (pending.current.scope===scope && pending.current.active))
      throw Error('Draft save already in progress')
    // The previous campaign/day may have committed an uncertain POST. Never
    // carry that old design ID or optimistic CAS revision into a new scope.
    if(ticket.current.scope!==scope) {
      ticket.current={scope,designId:null,revision:0}
    }
    pending.current={scope,active:true}
    setBusy(true);setMessage('')
    try {
      const submitted=validateFeature3Design(design)
      if (submitted.shop_id !== shopId ||
          submitted.layers.some(layer => layer.type === 'image' &&
            (!imageMap[layer.asset_id]?.complete ||
             !imageMap[layer.asset_id]?.naturalWidth ||
             !imageMap[layer.asset_id]?.naturalHeight))) {
        throw Error('Registered media must still be authorized')
      }
      const response=await feature3Api.saveDesign(
        shopId,campaignId,dayId,submitted,{
          designId:ticket.current.designId,
          expectedRevision:ticket.current.revision,
        })
      if(!currentScope(scope,provider)){
        throw Error('Private design context changed during an uncertain save')
      }
      ticket.current={scope,designId:response.design_id,revision:response.revision}
      setMessage('Private v2 design metadata saved at revision '+response.revision+
        '. Not a rendered, reviewed or publishable poster.')
      return response
    } catch (error) {
      if(currentScope(scope,provider))setMessage(error?.status === 409
        ? 'This revision is stale or no longer authorized. Refresh history; do not resend automatically.'
        : 'Save not confirmed. Do not retry blindly: it may already have committed. Read private history first.')
      throw error
    } finally {
      if(pending.current.scope===scope)pending.current.active=false
      if(currentScope(scope,provider))setBusy(false)
    }
  }
  if (!feature3Api || typeof feature3Api.listDesigns !== 'function' ||
      typeof feature3Api.saveDesign !== 'function') {
    return <p role="note">Authenticated v2 draft API not connected. Local
      CPU editor and day-bound JSON backup remain available.</p>
  }
  return <section aria-label="Private v2 poster drafts">
    <p role="note">Poster v2 saving requires authenticated shop membership and the
      new reviewed database migration. This does not use the v1 poster API.</p>
    <button type="button" disabled={disabled || busy} onClick={loadHistory}>
      Load privately saved v2 designs
    </button>
    {saved.length>0 && <label>Reopen editable v2 design
      <select defaultValue="" disabled={disabled || busy} onChange={restore}>
        <option value="">Select saved DRAFT</option>
        {saved.filter(d=>d.status==='DRAFT').map(d=>
          <option key={d.id} value={d.id}>Revision {d.revision} / {d.id.slice(0,8)}</option>)}
      </select>
    </label>}
    {typeof feature3Api.listGeneratedJobs === 'function' &&
      typeof feature3Api.getGeneratedImageDownload === 'function' && <>
      <div style={{display:'grid',gap:8,marginTop:16}}>
        <button type="button" disabled={disabled || busy} onClick={loadGenerated}>
          Check my generated private images
        </button>
        {generatedJobs.map(job=><div key={job.id}
          style={{display:'flex',gap:8,alignItems:'center',flexWrap:'wrap'}}>
          <span>Image job {job.id.slice(0,8)} — {job.status}</span>
          {job.status==='SUCCEEDED' && <button type="button"
            disabled={disabled || busy} onClick={()=>openGenerated(job.id)}>
            Request 60-second signed download
          </button>}
        </div>)}
        {visibleGeneratedLink && <a href={visibleGeneratedLink.url} target="_blank"
          rel="noopener noreferrer" download>
          Open private PNG (expires in 60 seconds; not approved for publishing)
        </a>}
      </div>
    </>}
    <Feature3StudioPanel
      key={reopened ? reopened.id+':'+reopened.revision : 'new-'+shopId+dayId}
      shopId={shopId} campaignId={campaignId} dayId={dayId}
      brandKit={brandKit} imageMap={imageMap} approvedModels={approvedModels}
      approvedContent={approvedContent} restoredDesign={reopened}
      disabled={disabled || busy} onSaveDesign={saveDesign}/>
    {message && <p role="status">{message}</p>}
  </section>
}
