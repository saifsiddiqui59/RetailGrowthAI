import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { useRetailAuth } from '../../auth/AuthProvider.jsx'
import { Button } from '../../components/ui/button.jsx'
import { Card } from '../../components/ui/card.jsx'
import './platform-operations.css'

const CATEGORIES = [
  ['all','All'],['onboarding','Onboarding'],['subscription','Subscriptions'],
  ['job','Failed jobs'],['queue','Queue health'],
]
const VIEWS = [['active','Active'],['unread','Unread'],['history','History']]
const PAGE_SIZE = 40

// Server owns all alert categories and read state. No localStorage, fake
// Azure health, browser service key or unauthenticated React-only checks.
export default function PlatformAlerts() {
  const { client, user } = useRetailAuth()
  const queryClient = useQueryClient()
  const [view,setView] = useState('active')
  const [category,setCategory] = useState('all')
  const [offset,setOffset] = useState(0)
  const [working,setWorking] = useState(null)
  const [actionError,setActionError] = useState('')
  // Never share a root inbox cache across authenticated principals. Keeping
  // previous filters/pages for only 20 seconds avoids redundant per-page
  // database RPCs while preserving an explicit server-refresh control.
  const queryRoot = ['platform-notifications', user?.id || null]
  const alertsQuery = useQuery({
    queryKey: [...queryRoot, view, category, offset],
    queryFn: () => client.listPlatformNotifications(view,category,PAGE_SIZE,offset),
    enabled: Boolean(user?.id),
    staleTime: 20_000,
    gcTime: 60_000,
    retry: false,
  })
  const loading = alertsQuery.isFetching || alertsQuery.isPending
  const error = alertsQuery.isError
    ? 'Platform notifications could not be verified. Check the database migration and your root authorization; zero alerts is NOT assumed.'
    : actionError
  // A failed refresh must never display older notification records as live.
  const data = alertsQuery.isError ? null : alertsQuery.data

  async function toggleRead(item) {
    if (working!==null) return
    setWorking(item.id)
    setActionError('')
    try {
      await client.setPlatformNotificationRead(item.id,!item.read_at)
      // Invalidate every cached filter/view for this root. The active query
      // refetches now; other filter views refetch when selected later.
      await queryClient.invalidateQueries({ queryKey: queryRoot })
    } catch {
      setActionError('The read status update or refresh could not be verified. Refresh before retrying.')
    } finally {setWorking(null)}
  }

  function chooseView(next) {setView(next);setOffset(0)}
  function chooseCategory(next) {setCategory(next);setOffset(0)}
  return <section className="platform-alert-page" aria-label="Super Admin notification center">
    <div className="page-heading">
      <div><div className="eyebrow">RETAILGROWTHAI / SUPER ADMIN</div>
        <h1>Notifications &amp; alerts</h1>
        <p className="lead">Persistent, per-admin read/unread history from verified RetailGrowthAI database events.</p>
      </div>
      <Button variant="outline" className="subtle-button" disabled={loading}
        onClick={()=>{setActionError('');alertsQuery.refetch()}}>Refresh alerts</Button>
    </div>
    <Card className="panel platform-alert-disclaimer">
      <strong>Monitoring scope:</strong> database job failures, persisted poison receipts,
      delayed queue outbox records, stale worker leases, account approvals and
      subscription dates. <strong>Azure infrastructure uptime and real queue depths are not connected.</strong>
      No emails or publishing actions are sent.
    </Card>
    {loading && <p role="status">Refreshing verified platform notifications…</p>}
    {error && <p className="notice-error" role="alert">{error}</p>}
    {data && !loading && <>
      <Card className="platform-alert-tally rg-platform-alert-summary" aria-label="Notification totals">
        <strong>{data.unread_active} unread / {data.total_active} active alerts</strong>
        <span>Database checked {new Date(data.database_checked_at).toLocaleString('en-IN')} · Azure telemetry unavailable</span>
      </Card>
      <div className="platform-alert-filters" role="group" aria-label="Notification view">
        {VIEWS.map(([value,label])=><button type="button" key={value} aria-pressed={view===value}
          onClick={()=>chooseView(value)}>{label}</button>)}
      </div>
      <div className="platform-alert-filters" role="group" aria-label="Notification category">
        {CATEGORIES.map(([value,label])=><button type="button" key={value} aria-pressed={category===value}
          onClick={()=>chooseCategory(value)}>{label}</button>)}
      </div>
      <div className="platform-alert-list">
        {!data.items.length && <p role="status">No matching verified notifications.</p>}
        {data.items.map(item=><article className={'platform-alert-item alert-'+
          (item.severity==='critical'?'action':item.severity==='attention'?'attention':'info')} key={item.id}>
          <div className="platform-alert-indicator" aria-hidden="true">{item.severity==='critical'?'!':item.severity==='attention'?'◷':'i'}</div>
          <div className="platform-alert-body">
            <small>{item.category} · {item.active?'Active':'Resolved'} · {item.read_at?'Read':'Unread'}</small>
            <h2>{item.title}</h2><p>{item.detail}</p>
            <small>First seen {new Date(item.first_seen_at).toLocaleString('en-IN')}</small>
          </div>
          <div className="platform-alert-actions">
            {['onboarding','subscription'].includes(item.category) &&
              <Link className="text-link" to="/platform-admin">
                {item.category==='onboarding'?'Review requests':'Manage subscriptions'} →
              </Link>}
            <button type="button" className="subtle-button"
              disabled={working!==null}
              aria-label={(item.read_at?'Mark unread':'Mark read')+' — '+item.title}
              onClick={()=>toggleRead(item)}>{item.read_at?'Mark unread':'Mark read'}</button>
          </div>
        </article>)}
      </div>
      <div className="platform-pager">
        <button type="button" className="subtle-button" disabled={offset===0}
          onClick={()=>setOffset(Math.max(0,offset-PAGE_SIZE))}>Previous</button>
        <span>Page {Math.floor(offset/PAGE_SIZE)+1} · {data.items.length} shown</span>
        <button type="button" className="subtle-button" disabled={data.items.length<PAGE_SIZE||offset>=100000-PAGE_SIZE}
          onClick={()=>setOffset(o=>o+PAGE_SIZE)}>Next</button>
      </div>
    </>}
  </section>
}
