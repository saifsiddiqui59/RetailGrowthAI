import {useState} from 'react'
import {Button} from '../../components/ui/button.jsx'
import {Badge} from '../../components/ui/badge.jsx'
import {Card} from '../../components/ui/card.jsx'
import {formatSchedule,normalizeSocialAccounts,normalizePublishingHistory,PROVIDER_LABELS} from './integration-read-model.mjs'
import {OFFLINE_SCENARIOS,offlineScenario} from './feature1-offline-fixtures.mjs'

// Both read views accept verified same-tenant records. Real Part 2 transport is
// deliberately NOT wired; examples cannot be interpreted as actual connected accounts.
export function SocialAccountReadView({shopId,records}){
 const [state,setState]=useState('all')
 let accounts
 try {accounts=normalizeSocialAccounts(shopId,records)} catch {
   return <p role="alert">Social account data could not be verified.</p>
 }
 const visible=state==='all'?accounts:accounts.filter(a=>a.status===state)
 return <div className="rg-f1-read-view" aria-label="Social account read preview">
  <label>Status <select aria-label="Social account status filter" value={state} onChange={e=>setState(e.target.value)}>
   <option value="all">All states</option>{['CONNECTED','DISCONNECTED','EXPIRED','REVOKED','PENDING'].map(s=><option value={s} key={s}>{s}</option>)}
  </select></label>
  <p role="status">{visible.length} accounts matching (offline input only)</p>
  <div className="rg-f1-read-grid">{visible.map(a=><Card key={a.id} className="rg-f1-read-card">
   <strong>{PROVIDER_LABELS[a.provider]}</strong> <Badge>{a.status}</Badge>
   <p>{a.channel_name}</p><small>Identity: {a.channel_id}</small>
   <p>Example scopes: {a.scopes.length?a.scopes.join(', '):'None'}</p>
   <small>Verified input: {formatSchedule(a.verified_at,'Asia/Kolkata')}</small>
   <div><Button variant="outline" size="sm" disabled>Connect / disconnect unavailable</Button></div>
  </Card>)}</div>
  {!visible.length&&<p>No example connections in this filter.</p>}
 </div>
}
export function PublishingReadView({shopId,records}){
 const [status,setStatus]=useState('all')
 const [page,setPage]=useState(0)
 let all
 try {all=normalizePublishingHistory(shopId,records)} catch {
  return <p role="alert">Publishing receipt data could not be verified.</p>
 }
 const selected=status==='all'?all:all.filter(item=>item.status===status)
 const pages=Math.max(1,Math.ceil(selected.length/8))
 const current=Math.min(page,pages-1)
 const shown=selected.slice(current*8,(current+1)*8)
 return <div className="rg-f1-read-view" aria-label="Publishing history read preview">
  <label>Delivery state <select aria-label="Publishing status filter" value={status} onChange={e=>{setStatus(e.target.value);setPage(0)}}>
   <option value="all">All states</option>
   {['SCHEDULED','QUEUED','PUBLISHING','PUBLISHED','FAILED','CANCELLED'].map(s=><option value={s} key={s}>{s}</option>)}
  </select></label>
  <p role="status">{selected.length} example events matching</p>
  <div className="rg-f1-read-grid">{shown.map(item=><Card key={item.id} className="rg-f1-read-card">
   <strong>{PROVIDER_LABELS[item.provider]} · {item.channel_name}</strong>
   <div><Badge>{item.status}</Badge></div>
   <p>{formatSchedule(item.scheduled_at,item.timezone)}</p>
   <small>Example attempts: {item.attempts}</small>
   {item.receipt_id&&<p>Example provider receipt: {item.receipt_id}</p>}
   {item.failure_code&&<p>Example failure: {item.failure_code}</p>}
  </Card>)}</div>
  {!shown.length&&<p>No example events in this filter.</p>}
  <nav className="rg-f1-read-pager" aria-label="Example publishing pages">
   <Button variant="outline" disabled={current===0} onClick={()=>setPage(x=>x-1)}>Previous sample page</Button>
   <span>Page {current+1} of {pages}</span>
   <Button variant="outline" disabled={current>=pages-1} onClick={()=>setPage(x=>x+1)}>Next sample page</Button>
  </nav>
 </div>
}
export function OfflineIntegrationPreview({section}){
 const [open,setOpen]=useState(false)
 const [shopId,setShopId]=useState(OFFLINE_SCENARIOS[0].id)
 const input=open?offlineScenario(shopId):null
 return <Card className="panel rg-f1-fixture-preview" aria-label="Offline test preview">
  <h2>Preview with fictional test inputs</h2>
  <p>Explore fully offline, tenant-scoped example screens. No provider identity, connection, successful post or receipt shown here belongs to your business.</p>
  <Button variant="outline" type="button" onClick={()=>setOpen(v=>!v)}>
    {open?'Hide offline test preview':'Open offline test preview'}
  </Button>
  {open&&<div className="rg-f1-fixture-content">
   <p className="rg-f1-fixture-warning" role="status"><strong>OFFLINE TEST ONLY — NOT LIVE DATA</strong> · Never use these samples as publishing evidence.</p>
   <label>Fictional business <select aria-label="Fictional business scenario" value={shopId} onChange={e=>setShopId(e.target.value)}>
    {OFFLINE_SCENARIOS.map(s=><option value={s.id} key={s.id}>{s.name}</option>)}
   </select></label>
   <div key={shopId}>
    {section==='connections'
      ?<SocialAccountReadView shopId={shopId} records={input.accounts}/>
      :<PublishingReadView shopId={shopId} records={input.history}/>}
   </div>
  </div>}
 </Card>
}
