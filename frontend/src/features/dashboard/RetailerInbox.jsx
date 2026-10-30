import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useRetailAuth } from '../../auth/AuthProvider.jsx'
import { useAuthorizedShops } from './useAuthorizedShops.js'
import { useSelectedShop } from './useSelectedShop.js'
import { Button } from '../../components/ui/button.jsx'
import { Card } from '../../components/ui/card.jsx'
import { Badge } from '../../components/ui/badge.jsx'

const categories = [['all','All'],['campaign','Campaigns'],['video','Videos'],['poster','Posters']]
const pageSize = 20
const guide = [
  ['Tenant-scoped events','Only real terminal campaign, Reel and poster jobs for a current active business membership appear.'],
  ['Verified delivery status','This inbox reports local database job states, never a social-network publish receipt or Azure service health.'],
  ['Read state','Read/unread is stored per signed-in user in the database; no browser-only unread total is inferred.'],
]

export default function RetailerInbox() {
  const { client, configured, user } = useRetailAuth()
  const queryClient = useQueryClient()
  const shopsQuery = useAuthorizedShops({client,configured,user})
  const shops = shopsQuery.isError ? [] : (shopsQuery.data || [])
  const { shopId, selectShop } = useSelectedShop({user,shops})
  const [view,setView] = useState('all')
  const [category,setCategory] = useState('all')
  const [page,setPage] = useState(0)
  const [working,setWorking] = useState(null)
  const [actionError,setActionError] = useState('')
  const rootKey = ['retailer-inbox',user?.id || null,shopId]
  const inboxQuery = useQuery({
    queryKey:[...rootKey,view,category,page],
    queryFn:()=>client.listRetailerInbox(shopId,view,category,pageSize,page*pageSize),
    enabled:Boolean(configured && user?.id && shopId),
    staleTime:20_000,
    gcTime:60_000,
    retry:false,
    refetchOnWindowFocus:false,
  })
  const error = shopsQuery.isError || inboxQuery.isError
  // A failed membership refresh must never expose a previously cached inbox.
  const data = error ? null : inboxQuery.data
  const loading = Boolean(shopsQuery.isFetching || inboxQuery.isFetching)
  async function toggle(item) {
    if (working!==null) return
    setWorking(item.id)
    setActionError('')
    try {
      await client.setRetailerInboxRead(shopId,item.id,!item.read_at)
      await queryClient.invalidateQueries({queryKey:rootKey})
    } catch {
      setActionError('The read update or verified refresh failed. Refresh before trying again.')
    } finally { setWorking(null) }
  }
  return <section className="rg-workspace-page rg-retailer-inbox" aria-label="Retailer notification center">
    <div className="page-heading">
      <div><div className="eyebrow">RETAILER INBOX</div><h1>Notifications</h1>
        <p className="lead">Private job updates for your selected business, backed by saved database events.</p></div>
      <Badge>No fabricated live data</Badge>
    </div>
    <Card className="panel rg-integration-guide" aria-label="Notifications integration requirements">
      <div className="eyebrow">VERIFICATION BOUNDARY</div>
      <h2>Verified event scope</h2>
      <ol className="rg-integration-steps">{guide.map(([title,detail],i)=>
        <li key={title}><span className="rg-integration-number" aria-hidden="true">{i+1}</span>
          <div><strong>{title}</strong><p>{detail}</p></div></li>)}</ol>
      <p className="rg-integration-safety" role="status">No connection, message, post, payment or scheduled delivery is created by viewing this guide.</p>
    </Card>
    <Card className="panel">
      {!configured && <p role="status">RetailGrowthAI Supabase is not configured. Inbox data is unavailable, not empty.</p>}
      {configured && user && <div className="rg-retailer-inbox-controls">
        <label>Business <select aria-label="Inbox business" value={shopId}
          onChange={e=>{selectShop(e.target.value);setPage(0);setActionError('')}}>
          {!shops.length && <option value="">No authorized business</option>}
          {shops.map(shop=><option key={shop.id} value={shop.id}>{shop.name}</option>)}
        </select></label>
        <label>View <select aria-label="Inbox view" value={view}
          onChange={e=>{setView(e.target.value);setPage(0)}}>
          <option value="all">All messages</option><option value="unread">Unread</option>
        </select></label>
        <label>Category <select aria-label="Inbox category" value={category}
          onChange={e=>{setCategory(e.target.value);setPage(0)}}>
          {categories.map(([id,label])=><option key={id} value={id}>{label}</option>)}
        </select></label>
        <Button variant="outline" disabled={!shopId || loading}
          onClick={()=>{setActionError('');inboxQuery.refetch()}}>Refresh inbox</Button>
      </div>}
      {loading && <p role="status">Checking your authorized inbox…</p>}
      {error && <p role="alert">Private notifications could not be verified. The inbox migration may not be deployed or your access may have changed. No zero unread count is assumed.</p>}
      {actionError && <p role="alert">{actionError}</p>}
      {configured && !shopsQuery.isPending && shops.length===0 && !error &&
        <p role="status">No authorized businesses. <Link to="/account">Review your account.</Link></p>}
      {data && !loading && <div className="rg-inbox-results">
        <p role="status"><strong>{data.unread_total} unread</strong> for this business · {data.matching_total} matching events</p>
        {data.items.length===0 && <p>No verified notifications in this view. Earlier jobs are not backfilled.</p>}
        <div className="rg-inbox-cards" aria-label="Verified retailer notifications">
        {data.items.map(item=><Card key={item.id} className="rg-inbox-item">
          <div><Badge>{item.category}</Badge> <Badge>{item.read_at?'Read':'Unread'}</Badge></div>
          <h2>{item.title}</h2><p>{item.detail}</p>
          <small>{new Date(item.created_at).toLocaleString('en-IN')}</small>
          <div className="rg-inbox-actions">
            <Button variant="outline" size="sm" disabled={working!==null}
              onClick={()=>toggle(item)}>{item.read_at?'Mark unread':'Mark read'}</Button>
            <Button asChild variant="outline" size="sm"><Link to="/campaigns">Review job</Link></Button>
          </div>
        </Card>)}
        </div>
        <nav className="rg-inbox-pager" aria-label="Retailer inbox pages">
          <Button variant="outline" disabled={page===0 || loading}
            onClick={()=>setPage(n=>Math.max(0,n-1))}>Previous</Button>
          <span>Page {page+1}</span>
          <Button variant="outline" disabled={loading || (page+1)*pageSize>=data.matching_total}
            onClick={()=>setPage(n=>n+1)}>Next</Button>
        </nav>
      </div>}
      <p className="rg-library-safety">New verified terminal database job events only. This is not email delivery, social publishing history, Azure health monitoring, or a hosted acceptance test.</p>
    </Card>
  </section>
}
