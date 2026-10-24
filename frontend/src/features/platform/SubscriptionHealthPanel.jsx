import { useEffect, useState } from 'react'
import { useRetailAuth } from '../../auth/AuthProvider.jsx'
import './subscription-health.css'

const PAGE=25
const STATUS=[
  ['all','All retailers'],['expiring','Due within 7 days'],
  ['expired','Expired'],['suspended','Suspended'],
  ['unknown','Needs verification'],['healthy','Other active'],
]

// This monitor is server-paginated and server-filtered across ALL shops.
// Platform summary counts come from the DB, never the currently loaded page.
export default function SubscriptionHealthPanel({onManage,refreshKey=0}) {
  const {client}=useRetailAuth()
  const [status,setStatus]=useState('all')
  const [input,setInput]=useState('')
  const [search,setSearch]=useState('')
  const [offset,setOffset]=useState(0)
  const [loading,setLoading]=useState(true)
  const [error,setError]=useState('')
  const [data,setData]=useState(null)
  const [reload,setReload]=useState(0)

  useEffect(()=>{
    let alive=true
    setLoading(true)
    setError('')
    setData(null)
    client.listPlatformSubscriptionWatch(status,search,PAGE,offset)
      .then(next=>{if(alive)setData(next)})
      .catch(()=>{if(alive)setError('Global subscription data cannot be verified. The migration or root authorization may be unavailable.')})
      .finally(()=>{if(alive)setLoading(false)})
    return ()=>{alive=false}
  },[client,status,search,offset,reload,refreshKey])

  const counts=data?.counts
  function changeStatus(value){setStatus(value);setOffset(0)}
  function submitSearch(event){event.preventDefault();setOffset(0);setSearch(input.trim())}
  return <section className="panel subscription-health" aria-label="Subscription health across all retailers">
    <div className="panel-heading"><div><div className="eyebrow">SAAS OWNER / ENTITLEMENTS</div>
      <h2>Subscription watch — all retailers</h2></div>
      <button type="button" className="subtle-button" disabled={loading} onClick={()=>setReload(v=>v+1)}>Refresh</button>
    </div>
    <p>Server-verified, full-platform counts and paginated retailer search. Monitors
      subscription entitlements; this does not charge customers or process auto-renewal.</p>
    {loading&&<p role="status">Loading global subscription health…</p>}
    {error&&<p role="alert" className="notice-error">{error} No zero totals are assumed.</p>}
    {data&&!loading&&<>
      <div className="subscription-health-counts" aria-label="Global subscription health">
        <div><strong>{counts.expiring}</strong><span>Due in 7 days</span></div>
        <div><strong>{counts.expired}</strong><span>Expired</span></div>
        <div><strong>{counts.suspended}</strong><span>Suspended</span></div>
        <div><strong>{counts.unknown}</strong><span>Unknown</span></div>
      </div>
      <p className="subscription-health-coverage">Across all {data.all_retailers} retailers ·
        {counts.healthy} other active · {data.total} match current filters.</p>
      <div className="subscription-health-controls">
        <label>Filter status<select value={status} onChange={e=>changeStatus(e.target.value)}>
          {STATUS.map(([key,label])=><option key={key} value={key}>{label}</option>)}
        </select></label>
        <form onSubmit={submitSearch}>
          <label>Search all retailers<input type="search" maxLength={80} value={input}
            onChange={e=>setInput(e.target.value)} placeholder="Retailer, slug or plan"/></label>
          <button className="subtle-button" type="submit">Search</button>
        </form>
      </div>
      {!data.shops.length&&<p role="status">No retailers match these filters.</p>}
      <div className="subscription-health-rows">
        {data.shops.map(row=><div key={row.shop_id} className="subscription-health-row">
          <div><strong>{row.name}</strong><small>{row.plan_code||'Unknown'} · {row.health}</small></div>
          <span>{row.valid_until?'Ends '+new Date(row.valid_until).toLocaleDateString('en-IN'):'Expiry unverified'}</span>
          <button type="button" className="subtle-button" onClick={()=>onManage(row)}>Manage plan</button>
        </div>)}
      </div>
      <div className="platform-pager">
        <button type="button" className="subtle-button" disabled={offset===0}
          onClick={()=>setOffset(o=>Math.max(0,o-PAGE))}>Previous</button>
        <span>Page {Math.floor(offset/PAGE)+1} · showing {data.shops.length} of {data.total} matches</span>
        <button type="button" className="subtle-button" disabled={offset+PAGE>=data.total||offset>=100000-PAGE}
          onClick={()=>setOffset(o=>o+PAGE)}>Next</button>
      </div>
    </>}
  </section>
}
